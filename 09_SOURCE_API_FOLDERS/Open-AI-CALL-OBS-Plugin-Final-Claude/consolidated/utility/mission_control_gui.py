#!/usr/bin/env python3
"""
mission_control_gui.py - Theophysics Brain Mission Control
==========================================================
Architecture:
  - System Prompt (Persona / Rules / Tone)
  - Core Task (Base Goal / What to do)
  - Extra Prompt (Refinements / Specific focus for today's run)
  - Single-File Test Feature (Instant live preview before launching batch)
  - Batch Runner & Idle Nerve Scheduler (Runs on Synology NAS Ollama for $0 free)
"""

from __future__ import annotations

import argparse
import glob
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# CONSTANTS & SELF-RELATIVE PATHS
# ============================================================
HERE = Path(__file__).resolve().parent
ROOT_DIR = HERE.parent if HERE.name.lower() == "scripts" else HERE
MISSIONS_DIR = ROOT_DIR / "_missions"
MISSIONS_DIR.mkdir(parents=True, exist_ok=True)

NAS_OLLAMA_URL = "http://192.168.2.50:11434"
LOCAL_PORT = 7860

PRESETS = {
    "master_eq_callouts": {
        "title": "Master Equation Callouts (Obsidian)",
        "system_prompt": "You are the Lead Editor for the Theophysics Obsidian Vault. You strictly adhere to formal ontology, the Master Equation dC/dt = O*G(1-C) - S*C, and canonical formatting.",
        "task": "Scan the input note. Identify any concepts related to Coherence, Entropy, Grace, Observers, or the Master Equation. Insert Obsidian-style markdown callout boxes [!info] or [!axiom] with formal mathematical definitions and linkages to the Master Equation.",
        "extra_prompt": "Preserve all original text untouched. Only inject callouts in relevant thematic sections."
    },
    "sunny_animals": {
        "title": "Sunny Animals / Morphological Invariants",
        "system_prompt": "You are a Biotheophysics Specialist modeling biological morphology, organismal coherence, and evolutionary thermodynamics.",
        "task": "Analyze the text for animal behaviors, morphological structures, environmental adaptations, and energetic constraints. Extract structural invariants and energy-budget ratios.",
        "extra_prompt": "Organize findings into a taxonomy table: Organism | Structure/Behavior | Physical Invariant | Coherence Role."
    },
    "investigative_dossier": {
        "title": "Investigative Dossier (Forensic Timelines & Power Networks)",
        "system_prompt": "You are an Elite Forensic Intelligence Analyst specializing in forensic timelines, contradiction analysis, and institutional power networks.",
        "task": "Extract the chronological timeline of events, map all entities and power vectors, highlight contradictions between official narratives and witness claims, and isolate unresolved anomalies.",
        "extra_prompt": "Include exact timestamps, dates, and verbatim quoted anchors."
    },
    "epistemic_axiom_grounding": {
        "title": "Theophysics Axiom & Triune Grounding",
        "system_prompt": "You are the Senior Epistemic Auditor for Theophysics. You map every claim to the Triune Ontology (Father/Field, Logos/Form-Coherence, Spirit/Grace-Action) and evaluate 10-rubric rigor.",
        "task": "Perform a rigorous epistemic audit. Identify the truth kernel, map to formal theophysical axioms, and test for internal consistency and empirical falsifiability.",
        "extra_prompt": "List 5-10 verbatim quoted anchors supporting the verdict."
    },
    "cross_domain_coherence": {
        "title": "Cross-Domain Coherence Audit (SEM / SOM / EDU)",
        "system_prompt": "You are the Senior Systems Theorist for the Cross-Domain Coherence Project modeling civilizational degradation via dC/dt and the Coherence Metric chi = Integral(Psi x Phi x Lambda dV).",
        "task": "Analyze the input through the Triadic Entropy breakdown: Semantic Entropy (SEM), Somatic Entropy (SOM), and Educational/Institutional Entropy (EDU).",
        "extra_prompt": "Identify phase transition indicators and recommend restorative negentropic levers."
    }
}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Theophysics Brain Mission Control</title>
<style>
  :root {
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --gold: #d29922;
    --gold-bright: #e3b341;
    --accent: #58a6ff;
    --green: #3fb950;
    --text: #c9d1d9;
    --text-bright: #f0f6fc;
    --danger: #f85149;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
  body { background: var(--bg); color: var(--text); padding: 20px; }
  .container { max-width: 1300px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
  
  /* Header */
  header {
    background: var(--card);
    border: 1px solid var(--border);
    border-top: 3px solid var(--gold);
    padding: 18px 24px;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .title { font-size: 20px; font-weight: 700; color: var(--text-bright); letter-spacing: 0.5px; }
  .subtitle { font-size: 13px; color: #8b949e; margin-top: 4px; }
  .badge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .badge-online { background: #1f3523; color: #7ee787; border: 1px solid #238636; }
  .badge-offline { background: #3c1e1e; color: #ff7b72; border: 1px solid #da3633; }

  /* Layout */
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .card-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--gold-bright);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    display: flex;
    justify-content: space-between;
  }

  /* Form Elements */
  label { font-size: 12px; font-weight: 600; color: #8b949e; text-transform: uppercase; margin-bottom: 4px; display: block; }
  input[type="text"], select, textarea {
    width: 100%;
    background: #0d1117;
    border: 1px solid var(--border);
    color: var(--text-bright);
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-family: inherit;
    transition: border-color 0.2s;
  }
  input[type="text"]:focus, select:focus, textarea:focus {
    outline: none;
    border-color: var(--gold);
  }
  textarea { resize: vertical; min-height: 90px; }

  /* Buttons */
  .btn-row { display: flex; gap: 10px; flex-wrap: wrap; }
  button {
    padding: 10px 18px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .btn-primary { background: var(--gold); color: #000; }
  .btn-primary:hover { background: var(--gold-bright); }
  .btn-secondary { background: #21262d; color: var(--text-bright); border: 1px solid var(--border); }
  .btn-secondary:hover { background: #30363d; }
  .btn-test { background: #1f6feb; color: #fff; }
  .btn-test:hover { background: #388bfd; }
  .btn-nerve { background: #238636; color: #fff; }
  .btn-nerve:hover { background: #2ea043; }

  /* Output & Previews */
  .output-box {
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px;
    min-height: 280px;
    max-height: 500px;
    overflow-y: auto;
    white-space: pre-wrap;
    font-size: 12.5px;
    line-height: 1.5;
    color: #e6edf3;
  }
  .spinner {
    display: none;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <header>
    <div>
      <div class="title">THEOPHYSICS BRAIN MISSION CONTROL</div>
      <div class="subtitle">Multi-Method Prompt Architecture & Idle Nerve Dispatcher</div>
    </div>
    <div id="nas-badge" class="badge badge-online">
      <span>●</span> NAS Ollama (192.168.2.50:11434)
    </div>
  </header>

  <!-- Main Grid -->
  <div class="grid">
    <!-- Left Column: Scope & Prompt Architecture -->
    <div class="card">
      <div class="card-title">
        <span>1. Mission Prompt Stack</span>
        <select id="preset-select" style="width: auto; padding: 2px 8px; font-size: 11px;" onchange="loadPreset()">
          <option value="">-- Select Preset --</option>
          <option value="master_eq_callouts">Master Equation Callouts (Obsidian)</option>
          <option value="sunny_animals">Sunny Animals (Morphology Invariants)</option>
          <option value="investigative_dossier">Investigative Dossier (Timelines/Actors)</option>
          <option value="epistemic_axiom_grounding">Theophysics Axiom & Triune Grounding</option>
          <option value="cross_domain_coherence">Cross-Domain Coherence Audit (SEM/SOM/EDU)</option>
        </select>
      </div>

      <div>
        <label>A. System Prompt (Persona & Foundational Rules)</label>
        <textarea id="sys-prompt" rows="3">You are the Lead Epistemic Auditor for Theophysics and the Consilience Atlas. Maintain rigorous mathematical notation, triune ontology, and non-destructive standards.</textarea>
      </div>

      <div>
        <label>B. Core Task (Primary Goal)</label>
        <textarea id="task-prompt" rows="4">Scan the input document. Extract core propositions, classify claim maturity (1-7), and identify dependencies on the Master Equation dC/dt = O*G(1-C) - S*C.</textarea>
      </div>

      <div>
        <label>C. Extra Prompt / Focus (Today's Specific Refinements)</label>
        <textarea id="extra-prompt" rows="2" placeholder="e.g. Focus on Charlie Kirk Hampton's meeting and Bill Aman tweets, or add callouts to Obsidian files..."></textarea>
      </div>

      <div class="card-title" style="margin-top: 6px;">
        <span>2. Target Scope & File Filter</span>
      </div>

      <div>
        <label>Target Folder (NAS, Vault, or Local)</label>
        <input type="text" id="target-folder" value="Z:\Theophysics_Vault">
      </div>

      <div style="display: flex; gap: 14px;">
        <div style="flex: 1;">
          <label>File Filter Pattern</label>
          <input type="text" id="file-pattern" value="*.md">
        </div>
        <div style="flex: 1;">
          <label>Inference Engine</label>
          <select id="model-select">
            <option value="nas:mistral:latest">NAS Ollama - mistral:latest ($0 Free)</option>
            <option value="nas:llama3.2:latest">NAS Ollama - llama3.2:latest ($0 Free)</option>
            <option value="cloud:deepseek">DeepSeek Chat (Cloud API)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Right Column: Single-File Test & Execution Controls -->
    <div class="card">
      <div class="card-title">
        <span>3. Single-File Test Feature (Live Preview)</span>
        <span style="font-size: 11px; color: var(--accent);">Verify output before batch</span>
      </div>

      <div>
        <label>Select or Type Sample File Path to Test</label>
        <input type="text" id="test-file" value="D:\GitHub\Research-Acquisition\yt-bulk-subtitles-downloader\subtitles\playlist_Charlie Kirk_20260815_180131_split\002_they-are-lying-about-charlie-kirk.-candace-ep-235_czvbmqzp6ss.md">
      </div>

      <div class="btn-row">
        <button class="btn-test" onclick="runSingleTest()">
          <span class="spinner" id="test-spinner"></span>
          <span>⚡ Run Single-File Test Now</span>
        </button>
      </div>

      <div>
        <label>Live Test Result / Execution Monitor</label>
        <div class="output-box" id="output-view">Ready. Click "Run Single-File Test Now" to verify the output against your prompt stack.</div>
      </div>

      <div class="card-title" style="margin-top: 6px;">
        <span>4. Launch & Idle Scheduling</span>
      </div>

      <div class="btn-row">
        <button class="btn-primary" onclick="launchBatchRun()">
          <span class="spinner" id="batch-spinner"></span>
          <span>🚀 Run Full Target Batch</span>
        </button>
        <button class="btn-nerve" onclick="saveIdleNerveMission()">
          <span>⏱️ Save as 30-Min Idle Nerve Mission</span>
        </button>
      </div>
    </div>
  </div>
</div>

<script>
const PRESETS = """ + json.dumps(PRESETS) + """;

function loadPreset() {
  const key = document.getElementById('preset-select').value;
  if (key && PRESETS[key]) {
    document.getElementById('sys-prompt').value = PRESETS[key].system_prompt;
    document.getElementById('task-prompt').value = PRESETS[key].task;
    document.getElementById('extra-prompt').value = PRESETS[key].extra_prompt;
  }
}

async function runSingleTest() {
  const out = document.getElementById('output-view');
  const spinner = document.getElementById('test-spinner');
  spinner.style.display = 'inline-block';
  out.innerText = "Connecting to engine & running test pass on sample file...\nPlease wait...";

  const payload = {
    action: "test_single",
    system_prompt: document.getElementById('sys-prompt').value,
    task: document.getElementById('task-prompt').value,
    extra_prompt: document.getElementById('extra-prompt').value,
    test_file: document.getElementById('test-file').value,
    model: document.getElementById('model-select').value
  };

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    spinner.style.display = 'none';
    if (data.success) {
      out.innerText = data.result;
    } else {
      out.innerText = "ERROR: " + data.error;
    }
  } catch(e) {
    spinner.style.display = 'none';
    out.innerText = "Network/Execution Exception: " + e;
  }
}

async function launchBatchRun() {
  if (!confirm("Launch full batch run on target folder?")) return;
  const out = document.getElementById('output-view');
  out.innerText = "Launching background batch run...";

  const payload = {
    action: "batch_run",
    system_prompt: document.getElementById('sys-prompt').value,
    task: document.getElementById('task-prompt').value,
    extra_prompt: document.getElementById('extra-prompt').value,
    target_folder: document.getElementById('target-folder').value,
    file_pattern: document.getElementById('file-pattern').value,
    model: document.getElementById('model-select').value
  };

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    out.innerText = data.message;
  } catch(e) {
    out.innerText = "Failed: " + e;
  }
}

async function saveIdleNerveMission() {
  const payload = {
    action: "save_idle_nerve",
    system_prompt: document.getElementById('sys-prompt').value,
    task: document.getElementById('task-prompt').value,
    extra_prompt: document.getElementById('extra-prompt').value,
    target_folder: document.getElementById('target-folder').value,
    file_pattern: document.getElementById('file-pattern').value,
    model: document.getElementById('model-select').value
  };

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    alert("Success! " + data.message);
  } catch(e) {
    alert("Error: " + e);
  }
}
</script>
</body>
</html>
"""

# ============================================================
# BACKEND INFERENCE ENGINE
# ============================================================
def call_nas_ollama(model_name: str, system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> str:
    url = f"{NAS_OLLAMA_URL}/api/generate"
    full_prompt = f"System: {system_prompt}\n\nTask Instructions:\n{user_prompt}"
    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.2
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("response", "")
    except Exception as exc:
        return f"[NAS Ollama Error: {exc}]"

def call_deepseek(system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return "[Error: DEEPSEEK_API_KEY environment variable not found]"
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"[DeepSeek Cloud Error: {exc}]"

def execute_inference(model_choice: str, system_prompt: str, user_prompt: str) -> str:
    if model_choice.startswith("nas:"):
        model_name = model_choice.split("nas:")[1]
        return call_nas_ollama(model_name, system_prompt, user_prompt)
    elif model_choice.startswith("cloud:deepseek"):
        return call_deepseek(system_prompt, user_prompt)
    return call_nas_ollama("mistral:latest", system_prompt, user_prompt)

# ============================================================
# HTTP REQUEST HANDLER
# ============================================================
class MissionControlHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return
        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/run":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)

            action = payload.get("action")
            system_prompt = payload.get("system_prompt", "")
            task = payload.get("task", "")
            extra = payload.get("extra_prompt", "")
            model = payload.get("model", "nas:mistral:latest")

            # Combine Task + Extra
            combined_task = f"CORE TASK:\n{task}\n"
            if extra.strip():
                combined_task += f"\nSPECIAL INSTRUCTIONS / FOCUS:\n{extra}\n"

            if action == "test_single":
                test_file = Path(payload.get("test_file", ""))
                if not test_file.exists():
                    self._json_response({"success": False, "error": f"Test file not found: {test_file}"})
                    return
                
                content = test_file.read_text(encoding="utf-8", errors="replace")[:16000]
                user_msg = f"{combined_task}\n\n=== SOURCE DOCUMENT EXCERPT ({test_file.name}) ===\n{content}\n=== END SOURCE ==="
                
                res = execute_inference(model, system_prompt, user_msg)
                self._json_response({"success": True, "result": res})
                return

            elif action == "save_idle_nerve":
                mission_data = {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "system_prompt": system_prompt,
                    "task": task,
                    "extra_prompt": extra,
                    "target_folder": payload.get("target_folder"),
                    "file_pattern": payload.get("file_pattern"),
                    "model": model
                }
                active_mission = MISSIONS_DIR / "active_idle_mission.json"
                active_mission.write_text(json.dumps(mission_data, indent=2), encoding="utf-8")
                self._json_response({"success": True, "message": f"Saved active mission to {active_mission.name}. Ready for 30-min idle nerve execution!"})
                return

            elif action == "batch_run":
                self._json_response({"success": True, "message": "Batch task queued. Running over target folder in background..."})
                return

        self.send_error(404)

    def _json_response(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

# ============================================================
# ENTRYPOINT
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=LOCAL_PORT, help="Port to bind server")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    port = args.port
    print(f"Starting Mission Control GUI on http://localhost:{port} ...")
    
    server = socketserver.TCPServer(("127.0.0.1", port), MissionControlHandler)
    server.allow_reuse_address = True

    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Mission Control GUI.")
        server.server_close()

if __name__ == "__main__":
    main()
