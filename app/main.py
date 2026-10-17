"""RootTrace 8D web app: JSON API under /api plus the static frontend."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import ROOT_DIR, Settings, load_settings
from app.ingest import (
    IngestError,
    check_size,
    normalize_image,
    parse_maintenance_log,
    parse_process_csv,
    read_complaint,
    summarize_dataset,
)
from app.llm.client import LLMClient
from app.llm.mock import MockLLM
from app.models import CaseView, ColumnMap, ImageMeta, SpecLimits
from app.numbers import allowed_values
from app.pipeline import case_context, containment_block, new_analysis, run_analysis
from app.report import SectionUpdateError, apply_section_update
from app.sample import build_case, load_cached_run, load_sample_inputs
from app.store import Case, CaseStore, ImageInput, new_case_id

log = logging.getLogger("roottrace")
STATIC_DIR = ROOT_DIR / "static"
MAX_IMAGES = 3


def error(status: int, code: str, message: str, details: list[str] | None = None) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


class AnalyzeRequest(BaseModel):
    mode: str = Field(default="live", pattern="^(live|cached)$")


class SectionPatch(BaseModel):
    content: str | None = Field(default=None, max_length=8000)
    approved: bool | None = None
    reviewer: str | None = Field(default=None, max_length=80)


class LiveThrottle:
    def __init__(self, limit: int, window_s: float, clock=time.monotonic):
        self.limit, self.window_s, self.clock = limit, window_s, clock
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self.clock()
        q = self.hits[key]
        while q and now - q[0] > self.window_s:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


def case_view(case: Case) -> dict:
    view = CaseView(
        id=case.id, is_sample=case.is_sample, title=case.title, created_at=case.created_at, meta=case.meta,
        spec=case.spec, columns=case.columns, dataset_summary=case.dataset_summary,
        ingest_warnings=case.ingest_warnings, complaint_text=case.complaint_text,
        images=[ImageMeta(index=im.index, filename=im.filename, url=f"/api/cases/{case.id}/images/{im.index}")
                for im in case.images],
        events=case.events, analysis=case.analysis, report=case.report,
    )
    return view.model_dump(mode="json")


def analysis_payload(case: Case) -> dict:
    data = case.analysis.model_dump(mode="json") if case.analysis else {}
    data["report"] = case.report.model_dump(mode="json") if case.report else None
    data["approved_count"] = case.report.approved_count if case.report else 0
    return data


def create_app(settings: Settings | None = None, llm: Any | None = None) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        client = app.state.llm
        if client is not None:
            await client.aclose()

    app = FastAPI(title="RootTrace 8D", version=settings.version, lifespan=lifespan,
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    app.state.settings = settings
    app.state.store = CaseStore(settings.case_ttl_s, settings.max_cases)
    app.state.llm = llm if llm is not None else (LLMClient(settings) if settings.mode == "live" else MockLLM(delay_s=0.4))
    app.state.mode = "live" if isinstance(app.state.llm, LLMClient) else "mock"
    app.state.sample = load_sample_inputs()
    app.state.cached_run = load_cached_run()
    app.state.throttle = LiveThrottle(settings.live_runs_per_ip, settings.live_window_s)

    # ------------------------------------------------------------------ errors
    @app.exception_handler(IngestError)
    async def _ingest_error(request: Request, exc: IngestError):
        return error(exc.status, exc.code, exc.message, exc.details)

    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return error(exc.status_code, exc.detail["code"], exc.detail["message"], exc.detail.get("details"))
        return error(exc.status_code, f"http_{exc.status_code}", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        details = [f"{'.'.join(str(p) for p in e.get('loc', []))}: {e.get('msg')}" for e in exc.errors()]
        return error(422, "invalid_request", "The request is not valid.", details)

    def get_case(case_id: str) -> Case:
        case = app.state.store.get(case_id)
        if case is None:
            raise HTTPException(404, {"code": "case_not_found", "message": "Case not found or expired. Reload the page."})
        return case

    # ------------------------------------------------------------------ API
    @app.get("/api/health")
    async def health():
        s = app.state.settings
        mode = app.state.mode
        cached = app.state.cached_run
        return {
            "status": "ok", "mode": mode, "version": s.version,
            "provider": s.provider_label if mode == "live" else "MOCK (not AMD)",
            "models": {"text": s.text.model if mode == "live" else "mock-deterministic",
                       "vision": s.vision.model if mode == "live" else "mock-deterministic"},
            "cached_run_available": cached is not None,
            "cached_run": {"recorded_at": cached.get("recorded_at"), "provider": cached.get("provider"),
                           "models": cached.get("models")} if cached else None,
        }

    @app.post("/api/cases/sample", status_code=201)
    async def create_sample():
        case = build_case(app.state.sample)
        app.state.store.add(case)
        return case_view(case)

    @app.post("/api/cases", status_code=201)
    async def create_case(
        process_csv: UploadFile = File(...),
        characteristic: str = Form(...),
        value_column: str = Form(...),
        complaint_text: str | None = Form(None),
        complaint_file: UploadFile | None = File(None),
        images: list[UploadFile] | None = File(None),
        maintenance_csv: UploadFile | None = File(None),
        unit: str = Form("mm"),
        lsl: float | None = Form(None),
        usl: float | None = Form(None),
        target: float | None = Form(None),
        timestamp_column: str = Form("timestamp"),
        lot_column: str = Form("lot"),
        title: str | None = Form(None),
    ):
        s = app.state.settings
        max_b = s.max_upload_bytes
        if lsl is not None and usl is not None and lsl >= usl:
            raise IngestError("Lower specification limit must be below the upper limit.")
        if lsl is None and usl is None:
            raise IngestError("Give at least one specification limit (LSL or USL).")
        images = [im for im in (images or []) if im is not None and im.filename]
        if len(images) > MAX_IMAGES:
            raise IngestError(f"At most {MAX_IMAGES} photos per case ({len(images)} uploaded).")
        text = ""
        if complaint_file is not None and complaint_file.filename:
            raw = await complaint_file.read()
            check_size(raw, max_b, "Complaint file")
            text = read_complaint(raw, complaint_file.filename)
        if complaint_text and complaint_text.strip():
            text = read_complaint(complaint_text) if not text else text
        if not text:
            raise IngestError("Provide the complaint text (paste it or upload a .txt/.eml file).")
        raw_csv = await process_csv.read()
        check_size(raw_csv, max_b, "Process data file")
        columns = ColumnMap(timestamp=timestamp_column.strip(), lot=lot_column.strip(), value=value_column.strip())
        df, params, warnings = parse_process_csv(raw_csv, columns)
        dropped = next((int(w.split()[0]) for w in warnings if "dropped" in w), 0)
        events = []
        if maintenance_csv is not None and maintenance_csv.filename:
            raw_log = await maintenance_csv.read()
            check_size(raw_log, max_b, "Maintenance log")
            events = parse_maintenance_log(raw_log)
        imgs = []
        for i, up in enumerate(images):
            raw_img = await up.read()
            imgs.append(ImageInput(index=i, filename=up.filename or f"photo{i + 1}.jpg",
                                   data=normalize_image(raw_img, up.filename or "", up.content_type, max_b)))
        spec = SpecLimits(characteristic=characteristic.strip() or "Measured characteristic", unit=unit.strip() or "",
                          lsl=lsl, usl=usl, target=target)
        case = Case(
            id=new_case_id(), is_sample=False, title=(title or f"{spec.characteristic}: custom case").strip()[:120],
            meta={"customer": "", "part_number": "", "part_name": "", "machine": ""}, spec=spec, columns=columns,
            baseline_end=None, complaint_text=text, images=imgs, df=df, parameters=params,
            dataset_summary=summarize_dataset(df, columns, params, dropped), events=events, ingest_warnings=warnings,
        )
        app.state.store.add(case)
        return case_view(case)

    @app.get("/api/cases/{case_id}")
    async def get_case_view(case_id: str):
        return case_view(get_case(case_id))

    @app.get("/api/cases/{case_id}/images/{index}")
    async def get_image(case_id: str, index: int):
        case = get_case(case_id)
        if not 0 <= index < len(case.images):
            raise HTTPException(404, {"code": "image_not_found", "message": "Image not found."})
        return Response(content=case.images[index].data, media_type="image/jpeg",
                        headers={"Cache-Control": "private, max-age=3600"})

    @app.post("/api/cases/{case_id}/analyze", status_code=202)
    async def start_analysis(case_id: str, request: Request, body: AnalyzeRequest | None = None):
        case = get_case(case_id)
        body = body or AnalyzeRequest()
        if case.analysis is not None and case.analysis.status == "running":
            raise HTTPException(409, {"code": "already_running", "message": "An analysis is already running for this case."})
        mode = body.mode
        notice = None
        if mode == "cached":
            if not case.is_sample:
                raise HTTPException(422, {"code": "cached_not_allowed",
                                          "message": "A cached AMD run exists only for the sample case."})
            if app.state.cached_run is None:
                raise HTTPException(409, {"code": "no_cached_run",
                                          "message": "No cached AMD run has been recorded yet; run live instead."})
        elif app.state.mode == "mock":
            mode = "mock"
        else:
            ip = request.client.host if request.client else "unknown"
            if not app.state.throttle.allow(ip):
                if case.is_sample and app.state.cached_run is not None:
                    mode, notice = "cached", "Live AMD runs are limited per visitor; showing the recorded AMD run."
                else:
                    raise HTTPException(429, {"code": "too_many_live_runs",
                                              "message": "Too many live analyses from your connection; try again in a few minutes."})
        async with case.lock:
            case.analysis = new_analysis(mode)
            case.report = None
            if notice:
                case.analysis.error = notice
            llm = app.state.llm
            case.task = asyncio.create_task(run_analysis(case, case.analysis, llm, app.state.cached_run))
        return analysis_payload(case)

    @app.get("/api/cases/{case_id}/analysis")
    async def poll_analysis(case_id: str):
        case = get_case(case_id)
        if case.analysis is None:
            raise HTTPException(404, {"code": "no_analysis", "message": "No analysis has been started for this case."})
        return analysis_payload(case)

    @app.patch("/api/cases/{case_id}/report/sections/{section_id}")
    async def patch_section(case_id: str, section_id: str, body: SectionPatch):
        case = get_case(case_id)
        if case.report is None:
            raise HTTPException(409, {"code": "no_report", "message": "Run the analysis first: there is no 8D draft yet."})
        allowed = None
        if case.analysis is not None and body.content is not None:
            allowed = allowed_values([e.text for e in case.analysis.evidence]
                                     + [case.complaint_text, containment_block(case, case.analysis), case_context(case)])
        try:
            section = apply_section_update(case.report, section_id.upper(), content=body.content,
                                           approved=body.approved, reviewer=body.reviewer, allowed=allowed)
        except KeyError:
            raise HTTPException(404, {"code": "section_not_found", "message": f"Unknown section '{section_id}'."})
        except SectionUpdateError as exc:
            raise HTTPException(422, {"code": "invalid_update", "message": str(exc)})
        data = section.model_dump(mode="json")
        data["approved_count"] = case.report.approved_count
        data["reviewer"] = case.report.reviewer
        return data

    # ------------------------------------------------------------------ frontend
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/report.html", include_in_schema=False)
    async def report_page():
        return FileResponse(STATIC_DIR / "report.html")

    return app


app = create_app()
