"""Station 5: async paper grading via LLMHub submit/collect flow."""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path

from ..llm_hub import LLMHub
from ..station_base import Manifest, StationBase, StationVerdict


class PaperGraderStation(StationBase):
    """Submit grade jobs on first pass and collect scored jobs on sweeps."""

    def __init__(self, input_dir: str, output_dir: str, queue_dir: str | None = None, **kwargs):
        super().__init__("paper-grader", input_dir, output_dir, file_extensions=[".md", ".txt"], **kwargs)
        self.hub = LLMHub(queue_dir=queue_dir or "_queue")

    def process(self, file_path: Path, manifest: Manifest) -> tuple[StationVerdict, float, str]:
        job_state_file = file_path.with_suffix(file_path.suffix + ".grade.json")
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if not job_state_file.exists() or json.loads(job_state_file.read_text(encoding="utf-8")).get("source_sha256") != digest:
            return self._submit(file_path, job_state_file)
        return self._collect(job_state_file)

    def _submit(self, file_path: Path, state_file: Path) -> tuple[StationVerdict, float, str]:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        job_id = self.hub.submit(
            station_name="paper-grader",
            file_path=str(file_path),
            prompt_name="grade_paper",
            backend="ollama",
            priority="standard",
            input_text=text,
        )
        state_file.write_text(json.dumps({"job_id": job_id, "status": "submitted", "source_sha256": hashlib.sha256(file_path.read_bytes()).hexdigest()}, indent=2), encoding="utf-8")
        return StationVerdict.HOLD, 0.0, f"submitted grade job {job_id}"

    def _collect(self, state_file: Path) -> tuple[StationVerdict, float, str]:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        job_id = state.get("job_id", "")
        completed = Path(self.hub.queue_dir) / "completed" / f"{job_id}.json"
        if not completed.exists():
            failed = Path(self.hub.queue_dir) / "failed" / f"{job_id}.json"
            if failed.exists():
                failure = json.loads(failed.read_text(encoding="utf-8"))
                return StationVerdict.REVIEW, 0.0, f"Grading incomplete: {failure.get('error', 'model job failed or requires review')}"
            return StationVerdict.HOLD, 0.0, f"waiting for completed/{job_id}.json"
        job = json.loads(completed.read_text(encoding="utf-8"))
        payload = self._extract_payload(job)
        try:
            score = float(payload.get("overall_score", payload.get("score")))
        except (TypeError, ValueError):
            return StationVerdict.REVIEW, 0.0, "Invalid grading response: missing numeric score"
        if not math.isfinite(score) or not 0 <= score <= 1:
            return StationVerdict.REVIEW, 0.0, "Invalid grading response: score must be between 0 and 1"
        verdict = StationVerdict.REVIEW
        if payload.get("verdict") in {"fail", "review"}:
            verdict = StationVerdict.REVIEW
        elif score >= self.threshold_pass:
            verdict = StationVerdict.PASS
        elif score <= self.threshold_fail:
            verdict = StationVerdict.FAIL
        state.update({"status": "collected", "score": score, "verdict": verdict.value, "payload": payload})
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return verdict, score, "graded via collected llm result"

    def _extract_payload(self, job: dict) -> dict:
        if isinstance(job.get("result_json"), dict) and job["result_json"]:
            return job["result_json"]
        result_text = str(job.get("result", ""))
        if "{" in result_text and "}" in result_text:
            try:
                return json.loads(result_text[result_text.index("{"): result_text.rindex("}") + 1])
            except Exception:
                return {}
        return {}
