"""Settings loaded from environment variables (and an optional local .env file)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from app import __version__

log = logging.getLogger("roottrace.config")

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader: KEY=VALUE lines, never overrides variables already set."""
    path = path or ROOT_DIR / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))  # type: ignore[arg-type]
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))  # type: ignore[arg-type]
    except ValueError:
        return default


@dataclass(frozen=True)
class RoleConfig:
    base_url: str | None
    api_key: str | None
    model: str | None

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


@dataclass(frozen=True)
class Settings:
    text: RoleConfig
    vision: RoleConfig
    provider_label: str
    llm_mode_setting: str
    max_concurrency: int
    max_rpm: int
    timeout_s: float
    max_attempts: int
    reasoning_effort: str | None
    case_ttl_s: int
    max_cases: int
    max_upload_mb: int
    live_runs_per_ip: int
    live_window_s: int
    version: str = __version__

    @property
    def mode(self) -> str:
        """`live` only when the text role is fully configured; otherwise `mock`."""
        if self.llm_mode_setting == "mock":
            return "mock"
        if self.text.ready:
            return "live"
        if self.llm_mode_setting == "live":
            log.warning("LLM_MODE=live but AMD_LLM_BASE_URL/AMD_LLM_API_KEY/AMD_TEXT_MODEL are incomplete; using mock")
        return "mock"

    def role(self, name: str) -> RoleConfig:
        return self.vision if name == "vision" else self.text

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def load_settings() -> Settings:
    load_dotenv()
    text = RoleConfig(
        base_url=_env("AMD_LLM_BASE_URL"),
        api_key=_env("AMD_LLM_API_KEY"),
        model=_env("AMD_TEXT_MODEL"),
    )
    vision = RoleConfig(
        base_url=_env("AMD_VISION_BASE_URL", text.base_url),
        api_key=_env("AMD_VISION_API_KEY", text.api_key),
        model=_env("AMD_VISION_MODEL", text.model),
    )
    mode = (_env("LLM_MODE", "auto") or "auto").lower()
    if mode not in {"auto", "live", "mock"}:
        mode = "auto"
    effort = _env("LLM_REASONING_EFFORT")
    return Settings(
        text=text,
        vision=vision,
        provider_label=_env("AMD_PROVIDER_LABEL", "AMD TokenFactory · AMD Instinct GPU") or "",
        llm_mode_setting=mode,
        max_concurrency=max(1, _int("LLM_MAX_CONCURRENCY", 8)),
        max_rpm=max(1, _int("LLM_MAX_RPM", 20)),
        timeout_s=max(5.0, _float("LLM_TIMEOUT_S", 90.0)),
        max_attempts=max(1, _int("LLM_MAX_ATTEMPTS", 3)),
        reasoning_effort=effort.lower() if effort else None,
        case_ttl_s=max(60, _int("CASE_TTL_S", 7200)),
        max_cases=max(10, _int("MAX_CASES", 300)),
        max_upload_mb=max(1, _int("MAX_UPLOAD_MB", 10)),
        live_runs_per_ip=max(1, _int("LIVE_RUNS_PER_IP", 5)),
        live_window_s=max(60, _int("LIVE_WINDOW_S", 600)),
    )
