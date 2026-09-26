"""Command Line Interface for lean-atom-extractor."""

import re
import sys
import click
from pathlib import Path
from typing import Optional

from .config import load_config
from .db.migrations import apply_migrations
from .db.repository import Repository, make_stable_id
from .scanner.file_scanner import FileScanner
from .scanner.extractor import LeanExtractor
from .runner.build_runner import BuildRunner
from .runner.auditor import TrustAuditor
from .ai.provider import AIProvider
from .exporter.atom_exporter import AtomExporter
from .web.app import run_server


@click.group()
@click.option("--config", "-c", "config_path", help="Path to config.toml", type=click.Path())
@click.option("--root", "-r", "root_dir", help="Lean project folder (overrides config.toml root_dir)",
              type=click.Path(exists=True, file_okay=False))
@click.option("--env", "env_dir", help="Lake project whose environment builds these files (default: the root)",
              type=click.Path(exists=True, file_okay=False))
@click.pass_context
def cli(ctx, config_path, root_dir, env_dir):
    """Lean 4 Corpus Scanner & Atom Record Extractor."""
    ctx.ensure_object(dict)
    cfg = load_config(config_path)
    if root_dir:
        new_root = Path(root_dir).resolve()
        if new_root != Path(cfg.project.root_dir).resolve():
            # A different Lean project gets its own project id in the registry.
            cfg.project.name = new_root.name
        cfg.project.root_dir = str(new_root)
    ctx.obj["config"] = cfg
    ctx.obj["env_dir"] = str(Path(env_dir).resolve()) if env_dir else None
    ctx.obj["repo"] = Repository(cfg.project.db_path)
    # Ensure migrations are applied
    apply_migrations(cfg.project.db_path)


# 1. SCAN
@cli.command()
@click.option("--force", "-f", is_flag=True, help="Force scan even if file hash is unchanged")
@click.pass_context
def scan(ctx, force):
    """Discover files, modules, namespaces, and declarations."""
    cfg = ctx.obj["config"]
    repo = ctx.obj["repo"]

    click.echo(f"Scanning Lean repository: {cfg.project.root_dir}")
    scanner = FileScanner(cfg.project.root_dir, cfg.scanner)
    files = scanner.scan()
    click.echo(f"Discovered {len(files)} .lean file(s).")

    # Upsert project
    proj_id = cfg.project.name
    repo.upsert_project(proj_id, cfg.project.name, cfg.project.root_dir)

    total_decls = 0
    scanned_files = 0
    skipped_files = 0

    for rel_path, fhash in files:
        rel_str = str(rel_path).replace("\\", "/")
        prev_hash = repo.get_source_file_hash(proj_id, rel_str)

        if not force and prev_hash == fhash:
            skipped_files += 1
            continue

        scanned_files += 1
        file_id = f"{proj_id}:{rel_str}"
        repo.upsert_source_file(file_id, proj_id, rel_str, fhash)

        # Read and extract
        abs_file = Path(cfg.project.root_dir) / rel_path
        try:
            with open(abs_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            click.echo(f"Error reading {rel_str}: {e}", err=True)
            continue

        extracted = LeanExtractor.extract_declarations(content, rel_str)
        for d in extracted:
            decl_id = make_stable_id(proj_id, rel_str, d["fully_qualified_name"])
            d["id"] = decl_id
            d["file_id"] = file_id
            d["project_id"] = proj_id
            repo.upsert_declaration(d)
            total_decls += 1

    click.echo(f"Scan complete: {scanned_files} files parsed, {skipped_files} unchanged files skipped, {total_decls} declarations indexed.")


# 2. CLASSIFY
@cli.command()
@click.pass_context
def classify(ctx):
    """Populate deterministic classifications for declarations."""
    repo = ctx.obj["repo"]
    decls = repo.list_declarations()
    click.echo(f"Classifying {len(decls)} declaration(s)...")

    count = 0
    for d in decls:
        kind = (d.get("declaration_kind") or "").lower()
        stmt = d.get("formal_statement") or ""

        # Deterministic role mapping. Nothing here has been compiled, so the
        # formal status stays NOT_BUILT until `verify` records a real build.
        formal_status = "NOT_BUILT"
        if kind == "axiom":
            logical_roles = ["PRIMITIVE"]
            statement_form = "UNCONDITIONAL"
        elif kind in ("theorem", "lemma"):
            logical_roles = ["DERIVED"]
            statement_form = "CONDITIONAL" if ("→" in stmt or "->" in stmt) else "UNCONDITIONAL"
        elif kind in ("def", "structure", "class", "inductive", "abbrev"):
            logical_roles = ["DEFINITIONAL"]
            statement_form = "UNCONDITIONAL"
        else:
            logical_roles = ["ASSUMPTION"]
            formal_status = "TARGET"
            statement_form = "UNCONDITIONAL"

        # Reasoning regime
        reasoning_regimes = ["CLASSICAL"] if "Classical" in stmt else ["CONSTRUCTIVE"]

        data = {
            "applicability": "FORMALIZABLE",
            "formalization_status": formal_status,
            "logical_roles": logical_roles,
            "reasoning_regimes": reasoning_regimes,
            "statement_form": statement_form,
            "formal_result": "NOT_BUILT",
            "trust_statuses": [],
            "correspondence_status": "PROPOSED"
        }
        repo.upsert_classification(d["id"], data)
        count += 1

    click.echo(f"Successfully classified {count} declaration(s).")


# 3. VERIFY
@cli.command()
@click.option("--file", "-f", "target_file", help="Compile specific file instead of entire project")
@click.pass_context
def verify(ctx, target_file):
    """Run Lean builds and record verification results and receipts."""
    cfg = ctx.obj["config"]
    repo = ctx.obj["repo"]
    runner = BuildRunner(cfg.project.root_dir, cfg.compiler, env_dir=ctx.obj.get("env_dir"))

    decls = repo.list_declarations(cfg.project.name)
    by_file = {}
    for d in decls:
        by_file.setdefault(d["relative_path"], []).append(d)
    files = [target_file.replace("\\", "/")] if target_file else sorted(by_file)

    # Each file is compiled on its own, and only its own declarations get
    # that file's result, so one broken file cannot mark everything failed
    # (or one good build mark everything passed).
    click.echo(f"Compiling {len(files)} file(s) with lake env lean...")
    tally = {}
    recorded = 0
    for n, rel in enumerate(files, 1):
        build_info = runner.run_target_build(rel)
        result = build_info["build_result"]
        tally[result] = tally.get(result, 0) + 1
        click.echo(f"  [{n}/{len(files)}] {result:<18} {rel}")
        if result != "PASSED":
            first_err = (build_info["stderr"] or build_info["stdout"]).strip().splitlines()[:1]
            if first_err:
                click.echo(f"      {first_err[0][:160]}")
        for d in by_file.get(rel, []):
            repo.record_build(d["id"], build_info)
            recorded += 1

    click.echo(f"Verification complete: {tally} | recorded on {recorded} declaration(s).")


# 4. AUDIT
@cli.command()
@click.pass_context
def audit(ctx):
    """Detect sorry, admit, custom axioms, and trust-boundary issues."""
    cfg = ctx.obj["config"]
    repo = ctx.obj["repo"]
    auditor = TrustAuditor(cfg.trust)

    decls = repo.list_declarations()
    click.echo(f"Auditing {len(decls)} declaration(s) for trust escapes...")

    escapes = 0
    axioms = 0
    for d in decls:
        finding = auditor.audit_declaration(d)
        repo.record_trust_finding(d["id"], finding)
        if finding["sorry_count"] > 0 or finding["admit_count"] > 0:
            escapes += 1
        if "CUSTOM_AXIOMS" in finding["trust_statuses"]:
            axioms += 1

    click.echo(f"Audit complete: {escapes} declarations contain sorry/admit escapes, {axioms} declared axioms flagged.")


# 5. ENRICH
@cli.command()
@click.option("--limit", "-n", default=10, help="Maximum declarations to enrich")
@click.pass_context
def enrich(ctx, limit):
    """Request optional AI semantic classifications."""
    cfg = ctx.obj["config"]
    if not cfg.ai.enabled:
        click.echo("AI enrichment is disabled in config.toml (ai.enabled = false). Set to true to enable.", err=True)
        return

    repo = ctx.obj["repo"]
    provider = AIProvider(cfg.ai)
    decls = repo.list_declarations()[:limit]

    click.echo(f"Enriching {len(decls)} declaration(s) via {cfg.ai.provider} ({cfg.ai.model})...")
    for d in decls:
        is_valid, res, reason = provider.enrich_declaration(d)
        if is_valid:
            click.echo(f"✓ Enriched: {d['fully_qualified_name']}")
        else:
            click.echo(f"✕ Quarantined: {d['fully_qualified_name']} ({reason})")


# 6. EXPORT
@cli.command()
@click.option("--out", "-o", default=None, help="Output directory for Atom JSON files")
@click.pass_context
def export(ctx, out):
    """Produce standardized Atom JSON files (Schema 1.0)."""
    cfg = ctx.obj["config"]
    repo = ctx.obj["repo"]
    export_dir = out or cfg.project.export_dir

    exporter = AtomExporter(export_dir)
    decls = repo.list_declarations()
    click.echo(f"Exporting {len(decls)} Atom JSON file(s) to {export_dir}...")

    exported = 0
    for d in decls:
        record = exporter.assemble_record(d)
        exporter.export_record(record)
        exported += 1

    click.echo(f"Successfully exported {exported} Atom JSON record(s).")


# 6b. PILLS
DEFAULT_SCAN_ROOTS = [
    r"D:\GitHub\Faith-through-physics-atoms",
    r"\\192.168.2.50\h_hp\Desktop\APIs\APIs\CLAIMS_PROOFS_EVIDENCE\CLAIM",
    r"\\192.168.2.50\h_hp\Desktop\APIs\APIs\CLAIMS_PROOFS_EVIDENCE\EVIDENCE",
    r"\\192.168.2.50\h_hp\Desktop\APIs\APIs\CKG\OUTBOX\CLAIMS_PROOFS_EVIDENCE",
]


@cli.command()
@click.option("--out", "-o", required=True, help="Folder to write proof pills into")
@click.option("--scan", "scan_roots", multiple=True,
              help="Other node folders to scan (read-only) for Lean mentions; repeatable")
@click.option("--no-scan", is_flag=True, help="Skip the cross-node mention scan")
@click.pass_context
def pills(ctx, out, scan_roots, no_scan):
    """Write YAML pills (theorems + Lean definitions), linked into one graph."""
    from .exporter.pill_exporter import export_pills
    cfg = ctx.obj["config"]
    roots = [] if no_scan else (list(scan_roots) or DEFAULT_SCAN_ROOTS)
    suffix = "" if cfg.project.name == "Theophysics" else "_" + re.sub(r"[^\w-]", "_", cfg.project.name)
    graph_copy = str(Path(cfg.project.db_path).resolve().parent / f"lean_graph{suffix}.json")
    counts = export_pills(ctx.obj["repo"], cfg.project.db_path, out, cfg.project.name,
                          scan_roots=roots, graph_copy=graph_copy)
    click.echo(f"Pills -> {out}: {counts}")
    click.echo(f"Graph for the API -> {graph_copy}")


# 6c. BRIEFS
@cli.command()
@click.option("--out", "-o", required=True, help="PROOF folder (briefs go in <out>/00_BRIEFS)")
@click.option("--workers", default=6, help="parallel DeepSeek calls")
@click.option("--force", is_flag=True, help="rewrite briefs even if the file is unchanged")
@click.pass_context
def briefs(ctx, out, workers, force):
    """Plain-language proof brief per Lean file (DeepSeek). Explanations, not evidence."""
    from .exporter.briefs import generate_briefs
    cfg = ctx.obj["config"]
    rels = sorted({d["relative_path"] for d in ctx.obj["repo"].list_declarations(cfg.project.name)})
    counts = generate_briefs(cfg.project.root_dir, rels, out, workers=workers, force=force)
    click.echo(f"Briefs -> {out}\\00_BRIEFS: {counts}")


# 7. SERVE
@cli.command()
@click.option("--port", "-p", default=None, type=int, help="Port to listen on")
@click.option("--host", "-h", default=None, help="Host to bind")
@click.option("--pills", "pills_dir", default=None, multiple=True, help="PROOF folder(s) with pills + 00_BRIEFS; repeatable")
@click.pass_context
def serve(ctx, port, host, pills_dir):
    """Launch the local searchable web interface."""
    cfg = ctx.obj["config"]
    h = host or cfg.web.host
    p = port or cfg.web.port
    run_server(cfg.project.db_path, cfg.project.export_dir, host=h, port=p, pills_dir=pills_dir)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
