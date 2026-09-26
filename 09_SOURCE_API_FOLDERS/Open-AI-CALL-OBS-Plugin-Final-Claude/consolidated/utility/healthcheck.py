"""
Healthcheck for One Page Paper API Pipeline
"""

import sys
import os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
TEMPLATES_DIR = SCRIPTS_DIR / "TEMPLATES"

def check():
    print("[1/5] Checking Python environment...")
    print(f"      Python version: {sys.version.split()[0]}")
    
    print("\n[2/5] Checking Required Packages...")
    for pkg in ["openpyxl", "requests", "yaml"]:
        try:
            __import__(pkg)
            print(f"      [OK] {pkg} is installed")
        except ImportError:
            print(f"      [--] Optional/Standard: {pkg} not found (using standard library fallbacks where applicable)")

    print("\n[3/5] Checking Pipeline Directories...")
    for folder in ["INBOX", "INBOX/_PRIORITY/SERIES", "INBOX/SERIES", "OUTBOX", "OUTBOX/MASTER_INDEX", "LOGS", "PROCESSED_ORIGINALS", "FAILED"]:
        p = ROOT_DIR / folder
        if p.exists():
            print(f"      [OK] {folder} exists")
        else:
            p.mkdir(parents=True, exist_ok=True)
            print(f"      [+] {folder} created")

    print("\n[4/5] Checking API_LAYER_v0.3 Templates...")
    required_templates = [
        "02_MASTER_PAPER_TEMPLATE_v0.4.md",
        "CLAIMS_LAYER_TEMPLATE_v0.3.md",
        "MASTER_INDEX_FORMAT_v0.3.md",
        "TAG_TAXONOMY_v0.3.md",
        "GRADING_LAYER_TEMPLATE_v0.3.md"
    ]
    all_templates_ok = True
    for t in required_templates:
        tp = TEMPLATES_DIR / t
        if tp.exists():
            print(f"      [OK] Template: {t} ({tp.stat().st_size} bytes)")
        else:
            print(f"      [FAIL] Missing template: {t}")
            all_templates_ok = False

    print("\n[5/5] Checking API Credentials...")
    keys = ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY"]
    found_any = False
    for k in keys:
        val = os.environ.get(k, "")
        if val:
            print(f"      [OK] Found environment variable: {k} (***{val[-4:] if len(val)>=4 else '***'})")
            found_any = True
        else:
            print(f"      [--] {k} not set in environment (can be passed via config/env)")

    print("\n" + "="*50)
    if all_templates_ok:
        print(" HEALTHCHECK PASSED: System ready for Turbo Intake Runs!")
    else:
        print(" HEALTHCHECK WARNING: Some template files need verification.")
    print("="*50)

if __name__ == "__main__":
    check()
