"""Subprocess runner for Lean 4 builds and toolchain verification."""

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import CompilerConfig


class BuildRunner:
    def __init__(self, root_dir: str, config: CompilerConfig, env_dir: Optional[str] = None):
        self.root_dir = Path(root_dir)
        self.config = config
        # Files may live outside a Lake project; they then build in env_dir's
        # environment (its toolchain + dependencies). Recorded in the receipt.
        self.env_dir = Path(env_dir) if env_dir else self.root_dir

    def get_toolchain_info(self) -> Dict[str, str]:
        """Fetch active Lean and Lake toolchain versions."""
        info = {"lean_version": "", "toolchain_version": ""}
        try:
            res = subprocess.run(
                [self.config.lean_cmd, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                cwd=str(self.env_dir),  # elan picks the project's lean-toolchain here
                shell=False
            )
            if res.returncode == 0:
                info["lean_version"] = res.stdout.strip()
        except Exception:
            pass

        try:
            res = subprocess.run(
                [self.config.lake_cmd, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                cwd=str(self.env_dir),  # elan picks the project's lean-toolchain here
                shell=False
            )
            if res.returncode == 0:
                info["toolchain_version"] = res.stdout.strip()
        except Exception:
            pass

        return info

    def run_target_build(self, target_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Run safe compilation without shell interpolation.
        If target_file provided, runs 'lean <target_file>', else 'lake build'.
        """
        toolchain = self.get_toolchain_info()
        checked_at = datetime.now(timezone.utc).isoformat()

        if target_file:
            # `lake env` puts the project's dependencies (e.g. Mathlib) on the
            # search path; plain `lean file` cannot resolve their imports.
            abs_target = (self.root_dir / target_file).resolve()
            cmd = [self.config.lake_cmd, "env", self.config.lean_cmd, str(abs_target)]
            cmd_str = f"lake env lean {target_file}" + (f"  (env {self.env_dir})" if self.env_dir != self.root_dir else "")
        else:
            cmd = [self.config.lake_cmd, "build"]
            cmd_str = "lake build"

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.env_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.timeout_seconds,
                shell=False
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

            if exit_code == 0:
                build_result = "PASSED"
            else:
                build_result = "FAILED"

        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if e.stdout else ""
            stderr = f"Build timed out after {self.config.timeout_seconds} seconds."
            exit_code = -1
            build_result = "TIMEOUT"
        except FileNotFoundError:
            stdout = ""
            stderr = f"Executable '{cmd[0]}' not found on system PATH."
            exit_code = -1
            build_result = "TOOLCHAIN_MISMATCH"
        except Exception as e:
            stdout = ""
            stderr = f"Subprocess error: {str(e)}"
            exit_code = -1
            build_result = "FAILED"

        # Compute deterministic receipt hash
        receipt_raw = f"{cmd_str}\n{exit_code}\n{stdout}\n{stderr}\n{checked_at}"
        receipt_hash = hashlib.sha256(receipt_raw.encode("utf-8")).hexdigest()

        return {
            "lean_version": toolchain["lean_version"],
            "toolchain_version": toolchain["toolchain_version"],
            "build_command": cmd_str,
            "build_result": build_result,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "receipt_hash": f"SHA256:{receipt_hash}",
            "checked_at": checked_at
        }
