from pathlib import Path
import csv
import json
import re
import threading
from typing import Dict, Any, List, Optional

INDEX_COLUMNS = [
    "paper_id", "source_sha256", "clean_title", "chapter", "content_type",
    "domain", "reader_category", "governing_question", "one_sentence_finding",
    "paper_rating", "rating_awarded_by", "evidence_status", "formal_status",
    "evd_state", "evd_support", "evd_counter", "evd_balance", "evd_families",
    "evd_coverage", "evd_gated", "evd_stable", "evd_weakest_claim", "coherence",
    "physical_event", "total_claims", "claims_with_falsifiers", "hidden_premises",
    "lean_targets_queued", "predictions_logged", "bridges_registered",
    "bridges_blank_lost", "truth_predicates", "source_paragraphs",
    "original_argument_steps", "total_argument_steps", "supplementary_arguments",
    "weak_links_identified", "semantic_provider", "semantic_model",
    "processed_date", "tags", "claim_ids", "lean_receipts"
]

def format_cell(value: Any) -> str:
    """Format a value safely for TSV output."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    s = str(value).replace("\t", " ").replace("\r\n", " ").replace("\n", " ").strip()
    return s

class MasterIndexWriter:
    def __init__(self, master_index_dir: Path):
        self.dir = master_index_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tsv_path = self.dir / "04_MASTER_INDEX.tsv"
        self.csv_path = self.dir / "04_MASTER_INDEX.csv"
        self._lock = threading.Lock()
        with self._lock:
            self._ensure_header()

    def _ensure_header(self):
        if not self.tsv_path.exists() or self.tsv_path.stat().st_size == 0:
            with open(self.tsv_path, "w", encoding="utf-8", newline="") as f:
                f.write("\t".join(INDEX_COLUMNS) + "\n")
        if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
            with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(INDEX_COLUMNS)

    def append_or_update(self, row_data: Dict[str, Any]) -> None:
        """Append or update a 43-column paper record keyed on source_sha256."""
        with self._lock:
            formatted_row = [format_cell(row_data.get(col, None)) for col in INDEX_COLUMNS]
            target_sha = str(row_data.get("source_sha256", "")).strip()

            # Read existing rows
            existing_rows: List[List[str]] = []
            header = None
            sha_idx = INDEX_COLUMNS.index("source_sha256")
            
            if self.tsv_path.exists():
                with open(self.tsv_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        header = lines[0].strip().split("\t")
                        for line in lines[1:]:
                            parts = line.strip().split("\t")
                            if len(parts) >= len(INDEX_COLUMNS):
                                existing_rows.append(parts[:len(INDEX_COLUMNS)])
                            elif parts and parts[0]:
                                parts.extend(["null"] * (len(INDEX_COLUMNS) - len(parts)))
                                existing_rows.append(parts)

            # Update if exists, else append
            updated = False
            if target_sha:
                for i, r in enumerate(existing_rows):
                    if len(r) > sha_idx and r[sha_idx] == target_sha:
                        existing_rows[i] = formatted_row
                        updated = True
                        break

            if not updated:
                existing_rows.append(formatted_row)

            # Write TSV (Primary Source of Truth)
            try:
                with open(self.tsv_path, "w", encoding="utf-8", newline="") as f:
                    f.write("\t".join(INDEX_COLUMNS) + "\n")
                    for r in existing_rows:
                        f.write("\t".join(r) + "\n")
            except Exception as e:
                print(f"    [Warning] Could not write TSV index: {e}")

            # Write CSV (Graceful fallback if file open in Excel)
            try:
                with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(INDEX_COLUMNS)
                    for r in existing_rows:
                        writer.writerow(r)
            except Exception as e:
                print(f"    [Notice] CSV index currently locked by external viewer (e.g. Excel); TSV updated successfully.")

            # Export Excel if openpyxl is available (Graceful fallback)
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "MASTER_INDEX"
                ws.append(INDEX_COLUMNS)
                for r in existing_rows:
                    ws.append(r)
                xlsx_path = self.dir / "04_MASTER_INDEX.xlsx"
                wb.save(xlsx_path)
            except Exception:
                pass
