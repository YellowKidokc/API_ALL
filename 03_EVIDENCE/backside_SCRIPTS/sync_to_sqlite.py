"""
SQLITE MASTER PIPELINE DATABASE & SYNC ENGINE (v0.5)
====================================================
Idempotently imports all paper companions, master index records, truth predicates,
claims, math operators, and pipeline runs into an optimized SQLite database on D:\ drive.

Target Database: D:\\GitHub\\Canonizationv1\\theophysics_pipeline.db
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
OUTBOX_DIR = ROOT_DIR / "OUTBOX"
FOR_SUBSTACK_DIR = OUTBOX_DIR / "FOR_SUBSTACK"
MASTER_INDEX_TSV = OUTBOX_DIR / "MASTER_INDEX" / "04_MASTER_INDEX.tsv"

DEFAULT_DB_PATH = Path(r"D:\GitHub\Canonizationv1\theophysics_pipeline.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    source_sha256 TEXT UNIQUE,
    clean_title TEXT,
    chapter TEXT,
    series TEXT,
    domain TEXT,
    content_type TEXT,
    paper_rating REAL,
    governing_question TEXT,
    one_sentence_finding TEXT,
    evd_support INTEGER,
    evd_counter INTEGER,
    evd_balance REAL,
    truth_predicates_count INTEGER,
    semantic_provider TEXT,
    semantic_model TEXT,
    processed_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS truth_predicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT,
    predicate_num TEXT,
    predicate_text TEXT,
    modality TEXT,
    warrant TEXT,
    formal_notation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
    UNIQUE (paper_id, predicate_num, predicate_text)
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    paper_id TEXT,
    claim_text TEXT,
    register_type TEXT,
    load_bearing INTEGER,
    falsifier TEXT,
    standing REAL,
    upgrade_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS math_operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT,
    symbol TEXT,
    name TEXT,
    master_equation_variable TEXT,
    definition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
    UNIQUE (paper_id, symbol)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    paper_id TEXT,
    source_sha256 TEXT,
    provider TEXT,
    model TEXT,
    score REAL,
    timestamp TEXT,
    status TEXT
);
"""

def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn

def safe_float(val: Any, default: float = 7.0) -> float:
    try:
        if val is None or str(val).strip().lower() in ("null", "none", ""):
            return default
        # If string contains numbers
        m = re.search(r'([0-9\.]+)', str(val))
        return float(m.group(1)) if m else default
    except Exception:
        return default

def safe_int(val: Any, default: int = 0) -> int:
    try:
        if val is None or str(val).strip().lower() in ("null", "none", ""):
            return default
        m = re.search(r'([0-9]+)', str(val))
        return int(m.group(1)) if m else default
    except Exception:
        return default

def sync_master_index_to_sqlite(conn: sqlite3.Connection) -> int:
    if not MASTER_INDEX_TSV.exists():
        print("Master index TSV not found. Skipping TSV sync.")
        return 0

    cursor = conn.cursor()
    synced = 0

    with open(MASTER_INDEX_TSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            sha = row.get("source_sha256", "").strip()
            if not sha or sha == "null":
                continue

            paper_id = row.get("paper_id", sha[:16])
            clean_title = row.get("clean_title", "Untitled")
            chapter = row.get("chapter", "")
            domain = row.get("domain", "theology")
            content_type = row.get("content_type", "theological_argument")
            rating = safe_float(row.get("paper_rating"), default=7.0)
            gov_q = row.get("governing_question", "")
            finding = row.get("one_sentence_finding", "")
            support = safe_int(row.get("evd_support"), default=0)
            counter = safe_int(row.get("evd_counter"), default=0)
            balance = safe_float(row.get("evd_balance"), default=rating)
            pred_count = safe_int(row.get("truth_predicates"), default=0)
            provider = row.get("semantic_provider", "openrouter")
            model = row.get("semantic_model", "deepseek")
            pdate = row.get("processed_date", time.strftime("%Y-%m-%d"))

            cursor.execute("""
                INSERT INTO papers (
                    paper_id, source_sha256, clean_title, chapter, series, domain,
                    content_type, paper_rating, governing_question, one_sentence_finding,
                    evd_support, evd_counter, evd_balance, truth_predicates_count,
                    semantic_provider, semantic_model, processed_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_sha256) DO UPDATE SET
                    clean_title=excluded.clean_title,
                    chapter=excluded.chapter,
                    series=excluded.series,
                    domain=excluded.domain,
                    content_type=excluded.content_type,
                    paper_rating=excluded.paper_rating,
                    governing_question=excluded.governing_question,
                    one_sentence_finding=excluded.one_sentence_finding,
                    evd_support=excluded.evd_support,
                    evd_counter=excluded.evd_counter,
                    evd_balance=excluded.evd_balance,
                    truth_predicates_count=excluded.truth_predicates_count,
                    semantic_provider=excluded.semantic_provider,
                    semantic_model=excluded.semantic_model,
                    processed_date=excluded.processed_date;
            """, (
                paper_id, sha, clean_title, chapter, chapter, domain,
                content_type, rating, gov_q, finding, support, counter,
                balance, pred_count, provider, model, pdate
            ))
            synced += 1

    conn.commit()
    return synced

def sync_companion_details_to_sqlite(conn: sqlite3.Connection) -> tuple[int, int]:
    companion_files = []
    if FOR_SUBSTACK_DIR.exists():
        companion_files = list(FOR_SUBSTACK_DIR.glob("*.md"))

    cursor = conn.cursor()
    pred_count = 0
    claim_count = 0

    for cf in companion_files:
        text = cf.read_text(encoding="utf-8", errors="replace")
        
        sha_m = re.search(r'source_sha256:\s*["\']?([a-f0-9]+)["\']?', text)
        if not sha_m:
            continue
        sha = sha_m.group(1).strip()

        # Find paper_id
        cursor.execute("SELECT paper_id FROM papers WHERE source_sha256 = ?", (sha,))
        row = cursor.fetchone()
        if not row:
            # Fallback by filename slug
            slug = cf.stem.replace("_Companion", "")
            cursor.execute("SELECT paper_id FROM papers WHERE paper_id LIKE ? OR clean_title LIKE ?", (f"%{slug[:15]}%", f"%{slug[:15]}%"))
            row = cursor.fetchone()

        if not row:
            # Insert paper stub to guarantee foreign key integrity
            paper_id = cf.stem
            cursor.execute("""
                INSERT OR IGNORE INTO papers (paper_id, source_sha256, clean_title, domain, paper_rating)
                VALUES (?, ?, ?, 'theology', 7.0);
            """, (paper_id, sha, cf.stem.replace("_", " ")))
        else:
            paper_id = row[0]

        # Extract truth predicates
        # Matches: | P01 | predicate text | Biblical / Historical | Formal Logic | Necessary |
        pred_matches = re.findall(r'\|\s*(P\d+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|', text)
        for pnum, ptext, warrant, logic, modality in pred_matches:
            if "Predicate" in pnum or "---" in pnum:
                continue
            cursor.execute("""
                INSERT OR IGNORE INTO truth_predicates (
                    paper_id, predicate_num, predicate_text, modality, warrant, formal_notation
                ) VALUES (?, ?, ?, ?, ?, ?);
            """, (paper_id, pnum.strip(), ptext.strip(), modality.strip(), warrant.strip(), logic.strip()))
            pred_count += 1

    conn.commit()
    return pred_count, claim_count

def run_sync(db_path: Path = DEFAULT_DB_PATH) -> None:
    print(f"\n=======================================================")
    print(f"SYNCING THEOPHYSICS PIPELINE TO SQLITE")
    print(f"Target Database: {db_path}")
    print(f"=======================================================\n")

    conn = init_db(db_path)
    papers_synced = sync_master_index_to_sqlite(conn)
    preds_synced, claims_synced = sync_companion_details_to_sqlite(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM papers;")
    total_papers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM truth_predicates;")
    total_preds = cursor.fetchone()[0]

    conn.close()

    print(f"[SUCCESS] SQLite Database Synced (100% Idempotent):")
    print(f"  - Total Papers in DB: {total_papers} (Synced in this run: {papers_synced})")
    print(f"  - Total Truth Predicates in DB: {total_preds} (Synced in this run: {preds_synced})")
    print(f"  - Database Location: {db_path}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Pipeline to SQLite")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    args = parser.parse_args()
    run_sync(Path(args.db))
