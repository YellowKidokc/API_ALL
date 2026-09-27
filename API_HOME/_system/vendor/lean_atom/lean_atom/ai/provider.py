"""AI Provider interface and schema validation."""

import json
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from ..config import AIConfig


class AISemanticsOutput(BaseModel):
    natural_language_statement: str = ""
    domains: list[str] = Field(default_factory=list)
    object_type: str = "CLAIM"
    role: str = "AX_DERIVED"
    correspondence_status: str = "PROPOSED"
    interpretation_boundary: str = ""
    proves: list[str] = Field(default_factory=list)
    does_not_prove: list[str] = Field(default_factory=list)
    bridge_candidates: list[str] = Field(default_factory=list)
    confidence: float = 0.85
    rationale: str = ""


class AIProvider:
    def __init__(self, config: AIConfig):
        self.config = config

    def build_prompt(self, decl: Dict[str, Any]) -> str:
        return f"""You are a formal logic and physics analyst. Analyze this Lean 4 declaration:
Declaration: {decl.get('declaration_kind')} {decl.get('fully_qualified_name')}
Formal Statement: {decl.get('formal_statement')}

Return ONLY valid JSON with this exact schema:
{{
  "natural_language_statement": "Plain English summary of claim",
  "domains": ["PHYSICS", "MATHEMATICS"],
  "object_type": "AXIOM" | "CLAIM" | "ATOM",
  "role": "AX_CORE" | "AX_DERIVED" | "AX_SCAFFOLD",
  "correspondence_status": "EXACT" | "PARTIAL" | "MODEL_ONLY" | "PROPOSED",
  "interpretation_boundary": "Physical / semantic limits",
  "proves": ["Precise scope proved in Lean"],
  "does_not_prove": ["What Lean does NOT prove"],
  "bridge_candidates": ["Proposed cross-domain links"],
  "confidence": 0.9,
  "rationale": "Reasoning for classification"
}}"""

    def call_ai(self, prompt: str) -> str:
        """Execute request to configured provider."""
        if self.config.provider == "ollama":
            url = f"{self.config.endpoint.rstrip('/')}/api/generate"
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "{}")

        elif self.config.provider in ("cloudflare", "openrouter"):
            url = self.config.endpoint
            payload = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]

        raise ValueError(f"Unsupported AI provider: {self.config.provider}")

    def enrich_declaration(self, decl: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Enrich declaration with AI.
        Returns: (is_valid, parsed_data_or_raw, quarantine_reason)
        """
        prompt = self.build_prompt(decl)
        input_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        try:
            raw_response = self.call_ai(prompt)
            output_hash = hashlib.sha256(raw_response.encode("utf-8")).hexdigest()

            # Validate against schema
            parsed_raw = json.loads(raw_response)
            validated = AISemanticsOutput(**parsed_raw)

            data = validated.model_dump()
            data.update({
                "provider": self.config.provider,
                "model": self.config.model,
                "prompt_version": self.config.prompt_version,
                "input_hash": f"SHA256:{input_hash}",
                "output_hash": f"SHA256:{output_hash}",
                "classified_at": datetime.now(timezone.utc).isoformat(),
                "review_status": "AI_PROPOSED"
            })
            return True, data, None

        except Exception as e:
            return False, {
                "provider": self.config.provider,
                "model": self.config.model,
                "prompt_version": self.config.prompt_version,
                "input_hash": f"SHA256:{input_hash}",
                "output_hash": "",
                "raw_response": str(e),
                "classified_at": datetime.now(timezone.utc).isoformat()
            }, f"Validation error: {str(e)}"
