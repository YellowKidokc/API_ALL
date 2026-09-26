"""Web server for lean-atom-extractor dashboard."""

import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional
from ..db.repository import Repository
from ..exporter.atom_exporter import AtomExporter


class WebHandler(SimpleHTTPRequestHandler):
    repo: Repository = None
    exporter: AtomExporter = None

    def __init__(self, *args, **kwargs):
        static_dir = str(Path(__file__).parent / "static")
        super().__init__(*args, directory=static_dir, **kwargs)

    graph: dict = None

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")  # other local stations can call it
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _find_node(self, key):
        g = self.graph or {}
        for n in g.get("nodes", []):
            if key in (n["node_id"], n["uuid"], n["name"]) or n["name"].endswith("." + key):
                return n
        return None

    def handle_graph_api(self, parsed):
        """Lean graph API for other stations.

        /api/lean/node?id=<node_id|uuid|name>   one node + its links
        /api/lean/search?q=<text>&lane=<lane>    find nodes
        /api/lean/graph                          everything
        """
        if not self.graph:
            return self._json({"error": "no lean_graph.json yet - run `lean-atom pills`"}, 503)
        q = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/api/lean/graph":
            return self._json(self.graph)
        if parsed.path == "/api/lean/node":
            node = self._find_node((q.get("id") or [""])[0])
            if not node:
                return self._json({"error": "not found"}, 404)
            nid = node["node_id"]
            edges = self.graph["edges"]
            return self._json({
                "node": node,
                "uses": [e["to"] for e in edges if e["from"] == nid and e["type"] == "uses"],
                "used_by": [e["from"] for e in edges if e["to"] == nid and e["type"] == "uses"],
                "mentioned_in": [{"node_id": e["from"], "file": e.get("file")}
                                 for e in edges if e["to"] == nid and e["type"] == "mentions"],
            })
        if parsed.path == "/api/lean/search":
            text = (q.get("q") or [""])[0].lower()
            lane = (q.get("lane") or [None])[0]
            hits = [n for n in self.graph["nodes"]
                    if text in n["name"].lower() and (not lane or n["lane"] == lane)]
            return self._json({"count": len(hits), "nodes": hits[:200]})
        return self._json({"error": "unknown endpoint"}, 404)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/lean/"):
            self.handle_graph_api(parsed)
        elif parsed.path == "/api/brief":
            self.handle_api_brief(parsed)
        elif parsed.path == "/api/declarations":
            self.handle_api_declarations()
        elif parsed.path == "/" or parsed.path == "/index.html":
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/export":
            self.handle_api_export(parsed)
        else:
            self.send_error(404, "Endpoint not found")

    pills_dir: Optional[Path] = None
    briefs: dict = None          # lean file -> brief json
    lines: dict = None           # (file, short name) -> {plain, role, brief}

    def _enrich(self, decls):
        """Add lane, plain meaning, brief facts and links from the pills/graph."""
        g = self.graph or {"nodes": [], "edges": []}
        by_id = {n["node_id"]: n for n in g["nodes"]}
        uses, used_by, mentions = {}, {}, {}
        for e in g["edges"]:
            if e["type"] == "uses":
                uses.setdefault(e["from"], []).append(e["to"])
                used_by.setdefault(e["to"], []).append(e["from"])
            else:
                mentions[e["to"]] = mentions.get(e["to"], 0) + 1
        for d in decls:
            nid = f"tp:lean/{d.get('project_id')}/{d['fully_qualified_name']}"
            node = by_id.get(nid, {})
            d["node_id"] = nid
            d["lane"] = node.get("lane")
            d["uses"] = uses.get(nid, [])
            d["used_by"] = used_by.get(nid, [])
            d["mention_count"] = mentions.get(nid, 0)
            ln = (self.lines or {}).get((d["relative_path"], d["declaration_name"]))
            d["meaning"] = ln["plain"] if ln else None
            d["meaning_role"] = ln.get("role") if ln else None
            b = (self.briefs or {}).get(d["relative_path"])
            if b:
                d["brief_md"] = b["_md"]
                d["brief_title"] = b.get("title")
                d["brief_does_not_prove"] = b.get("does_not_prove", [])
                d["brief_model"] = b.get("_model")
        return decls

    def handle_api_brief(self, parsed):
        name = (urllib.parse.parse_qs(parsed.query).get("name") or [""])[0]
        if not self.pills_dir or not name or "/" in name or "\\" in name or ".." in name:
            return self._json({"error": "bad name"}, 400)
        path = next((d / "00_BRIEFS" / name for d in (getattr(self, "pills_dirs", None) or [self.pills_dir])
                     if (d / "00_BRIEFS" / name).exists()), self.pills_dir / "00_BRIEFS" / name)
        if not path.exists():
            return self._json({"error": "not found"}, 404)
        return self._json({"name": name, "markdown": path.read_text(encoding="utf-8")})

    def handle_api_declarations(self):
        try:
            decls = self._enrich(self.repo.list_declarations())
            body = json.dumps({"declarations": decls}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")

    def handle_api_export(self, parsed):
        try:
            query = urllib.parse.parse_qs(parsed.query)
            decl_id = query.get("id", [None])[0]
            if not decl_id:
                self.send_error(400, "Missing 'id' parameter")
                return

            row = self.repo.get_declaration(decl_id)
            if not row:
                self.send_error(404, "Declaration not found")
                return

            record = self.exporter.assemble_record(row)
            out_path = self.exporter.export_record(record)

            body = json.dumps({"status": "ok", "path": str(out_path)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")


def _load_briefs(pills_dir: Path):
    briefs = {}
    bdir = pills_dir / "00_BRIEFS"
    if bdir.exists():
        for p in bdir.glob("*.brief.json"):
            try:
                b = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                continue
            b["_md"] = p.name.replace(".brief.json", ".md")
            for rel in [b["file"]] + b.get("also_in", []):
                briefs[rel] = b
    return briefs


def run_server(db_path: str, export_dir: str, host: str = "127.0.0.1", port: int = 8989,
               pills_dir: Optional[str] = None):
    """Launch quiet local server."""
    dirs = [pills_dir] if isinstance(pills_dir, str) else list(pills_dir or [])
    dirs = [Path(d) for d in dirs if d and Path(d).exists()]
    if dirs:
        from ..exporter.briefs import load_theorem_lines
        WebHandler.pills_dir = dirs[0]
        WebHandler.pills_dirs = dirs
        WebHandler.briefs, WebHandler.lines = {}, {}
        for d in dirs:
            WebHandler.briefs.update(_load_briefs(d))
            WebHandler.lines.update(load_theorem_lines(str(d)))
        print(f"Briefs loaded from {len(dirs)} folder(s): {len(set(b['file'] for b in WebHandler.briefs.values()))} files, "
              f"{len(WebHandler.lines)} explained declarations")
    repo = Repository(db_path)
    exporter = AtomExporter(export_dir)

    WebHandler.repo = repo
    WebHandler.exporter = exporter
    # One graph file per project (lean_graph.json, lean_graph_<project>.json); serve them merged.
    merged = {"nodes": [], "edges": [], "projects": []}
    for gp in sorted(Path(db_path).resolve().parent.glob("lean_graph*.json")):
        g = json.loads(gp.read_text(encoding="utf-8"))
        merged["nodes"] += g.get("nodes", [])
        merged["edges"] += g.get("edges", [])
        merged["projects"].append(g.get("project"))
    if merged["nodes"]:
        WebHandler.graph = merged
        print(f"Lean graph API loaded: {len(merged['nodes'])} nodes, {len(merged['edges'])} edges from "
              f"{merged['projects']}  (/api/lean/node, /api/lean/search, /api/lean/graph)")

    server = HTTPServer((host, port), WebHandler)
    print(f"Lean 4 Atom Registry Explorer running at: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
