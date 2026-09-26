"""The sole resolver for paths used by ONE_MENU."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

API_HOME = Path(__file__).resolve().parents[1]
CONFIG_DIR = API_HOME / "config"

class PathConfigurationError(RuntimeError):
    pass

def inside(*parts: str) -> Path:
    """Resolve a path owned by API_HOME and reject traversal outside it."""
    candidate = API_HOME.joinpath(*parts).resolve()
    try:
        candidate.relative_to(API_HOME)
    except ValueError as exc:
        raise PathConfigurationError(f"Internal path escapes API_HOME: {candidate}") from exc
    return candidate

def config_file() -> Path:
    override = os.environ.get("ONE_MENU_PATHS_FILE")
    return Path(override).expanduser().resolve() if override else CONFIG_DIR / "paths.json"

def load_paths(*, allow_example: bool = True) -> dict[str, str]:
    path = config_file()
    if not path.exists() and allow_example:
        path = CONFIG_DIR / "paths.example.json"
    if not path.exists():
        raise PathConfigurationError("Run RELOCATE.bat to create config/paths.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PathConfigurationError(f"{path} must contain a JSON object")
    return {str(k): str(v) for k, v in data.items()}

def external(key: str, *parts: str, required: bool = True) -> Path:
    raw = load_paths().get(key, "").strip()
    env_raw = os.environ.get(f"ONE_MENU_{key.upper()}", "").strip()
    raw = env_raw or raw
    if not raw:
        if required:
            raise PathConfigurationError(f"External path '{key}' is not configured; run RELOCATE.bat")
        return Path()
    base = Path(os.path.expandvars(raw)).expanduser()
    result = base.joinpath(*parts)
    if required and not base.exists():
        raise PathConfigurationError(f"External path '{key}' does not exist: {base}")
    return result

def ensure_runtime_dirs() -> None:
    for name in ("LOGS", "STATE"):
        inside(name).mkdir(parents=True, exist_ok=True)
