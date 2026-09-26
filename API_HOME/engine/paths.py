"""The only place ONE_MENU resolves paths.

Inside API_HOME everything is relative to this file, so the folder can be copied
anywhere. Everything outside API_HOME is a named key in config/paths.json
(git-ignored; config/paths.example.json ships the keys). A value may be:
  * absolute                      D:/Theophysics/papers
  * relative to API_HOME          ../PAPERS          (moves with the folder)
  * using env vars or ~           %USERPROFILE%/papers, ~/papers
The environment variable ONE_MENU_<KEY> overrides a single key for one run.
config/path_keys.json describes each key: what it is for and a fingerprint file
RELOCATE uses to find it again after a move.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

API_HOME = Path(__file__).resolve().parents[1]
CONFIG_DIR = API_HOME / "config"


class PathConfigurationError(RuntimeError):
    pass


def inside(*parts: str) -> Path:
    """A path owned by API_HOME. Refuses to escape the folder."""
    candidate = API_HOME.joinpath(*parts).resolve()
    try:
        candidate.relative_to(API_HOME)
    except ValueError as exc:
        raise PathConfigurationError(f"Internal path escapes API_HOME: {candidate}") from exc
    return candidate


def config_file() -> Path:
    override = os.environ.get("ONE_MENU_PATHS_FILE")
    return Path(override).expanduser().resolve() if override else CONFIG_DIR / "paths.json"


def key_specs() -> dict[str, dict]:
    return json.loads((CONFIG_DIR / "path_keys.json").read_text(encoding="utf-8"))


def load_paths(*, allow_example: bool = True) -> dict[str, str]:
    path = config_file()
    if not path.exists() and allow_example:
        path = CONFIG_DIR / "paths.example.json"
    if not path.exists():
        raise PathConfigurationError("Run RELOCATE.bat to create config/paths.json")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise PathConfigurationError(f"{path} must contain a JSON object")
    return {str(k): str(v) for k, v in data.items() if not str(k).startswith("_")}


def expand(raw: str) -> Path:
    """Expand env vars and ~; anchor relative values at API_HOME."""
    value = os.path.expandvars(raw.strip())
    # %VAR% is not expanded by os.path.expandvars on POSIX; handle it everywhere.
    while "%" in value:
        start = value.find("%")
        end = value.find("%", start + 1)
        if end < 0:
            break
        name = value[start + 1:end]
        value = value[:start] + os.environ.get(name, "") + value[end + 1:]
    path = Path(value).expanduser()
    return path if path.is_absolute() or value[1:3] in (":\\", ":/") else (API_HOME / path).resolve()


def raw_value(key: str) -> str:
    return (os.environ.get(f"ONE_MENU_{key.upper()}", "").strip()
            or load_paths().get(key, "").strip())


def external(key: str, *parts: str, required: bool = True, create: bool = False) -> Path:
    raw = raw_value(key)
    if not raw:
        if required:
            raise PathConfigurationError(f"Path '{key}' is not configured. Run RELOCATE.bat.")
        return Path()
    base = expand(raw)
    spec = key_specs().get(key, {})
    if (create or spec.get("create")) and not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    if spec.get("file") and not base.exists() and key == "catalog_db":
        base.parent.mkdir(parents=True, exist_ok=True)
        return base.joinpath(*parts)
    if required and not base.exists():
        raise PathConfigurationError(f"Path '{key}' does not exist: {base}. Run RELOCATE.bat.")
    return base.joinpath(*parts)


def configured(key: str) -> bool:
    raw = raw_value(key)
    return bool(raw) and expand(raw).exists()


def ensure_runtime_dirs() -> None:
    for name in ("LOGS", "STATE"):
        inside(name).mkdir(parents=True, exist_ok=True)
