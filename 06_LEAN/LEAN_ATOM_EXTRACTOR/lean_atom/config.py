"""Configuration loader for lean-atom-extractor."""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class ProjectConfig(BaseModel):
    name: str = "Theophysics"
    root_dir: str = "d:/GitHub/Faith-Thru-Physics-Lean-4-"
    db_path: str = "lean_atoms.db"
    export_dir: str = "./exports"


class ScannerConfig(BaseModel):
    approved_dirs: List[str] = Field(default_factory=lambda: ["."])
    exclude_dirs: List[str] = Field(
        default_factory=lambda: [".lake", ".git", "build", "cache", ".github", "lake-packages"]
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["*.compile.txt", "*_audit.md", "*.tmp"]
    )


class CompilerConfig(BaseModel):
    lean_cmd: str = "lean"
    lake_cmd: str = "lake"
    timeout_seconds: int = 60
    enable_verification: bool = True


class TrustConfig(BaseModel):
    flag_sorry: bool = True
    flag_admit: bool = True
    flag_custom_axioms: bool = True
    flag_unsafe: bool = True


class AIConfig(BaseModel):
    enabled: bool = False
    provider: str = "ollama"
    endpoint: str = "http://127.0.0.1:11434"
    model: str = "qwen3:4b-instruct"
    prompt_version: str = "v1.0-formal-semantic"
    max_batch_size: int = 10
    timeout_seconds: int = 30
    rate_limit_rpm: int = 60


class WebConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8989
    debug: bool = False


class AppConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    compiler: CompilerConfig = Field(default_factory=CompilerConfig)
    trust: TrustConfig = Field(default_factory=TrustConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    web: WebConfig = Field(default_factory=WebConfig)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from file or default."""
    if not config_path:
        search_paths = [
            Path("config.toml"),
            Path(__file__).parent.parent / "config.toml",
            Path.home() / ".lean_atom" / "config.toml"
        ]
        for p in search_paths:
            if p.exists():
                config_path = str(p)
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return AppConfig(**data)

    return AppConfig()
