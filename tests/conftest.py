import os

# Tests never call a real endpoint: force mock mode before the app module is imported.
os.environ["LLM_MODE"] = "mock"
os.environ.pop("AMD_LLM_API_KEY", None)
