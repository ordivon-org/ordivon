#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPO_ROOT / "creative-library" / "web"
DERIVED_ROOT = REPO_ROOT / "artifacts" / "creative-library" / "derived"
DEFAULT_ARCHIVE_JSON = Path("artifacts/creative-archive/historical-works-r2-source-complete.json")
DEFAULT_DERIVED_MANIFEST = Path("artifacts/creative-library/derived/manifest-v1.json")
DEFAULT_CATALOG = Path("artifacts/creative-library/catalog-v1.json")

# Presentation-only routing hints. These suffix mappings are deliberately NOT
# preservation format identification. PRONOM/Siegfried (or another external
# preservation identifier) owns format identity; this table only selects a
# reasonable browser presentation path when rendering the local library.
PRESENTATION_KIND_EXTENSIONS = {
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"},
    "audio": {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"},
    "video": {".mp4", ".webm", ".mov", ".mkv"},
    "html": {".html", ".htm"},
    "pdf": {".pdf"},
    "cad": {".step", ".stp", ".stl", ".obj", ".3mf", ".fcstd"},
    "eda": {".kicad_pcb", ".kicad_sch", ".sch", ".pcb", ".cir", ".spice", ".raw", ".gbr", ".gbrjob", ".drl"},
    "godot": {".godot", ".tscn", ".gd", ".glb", ".gltf"},
    "text": {".md", ".mdx", ".txt", ".typ", ".json", ".csv", ".tsv", ".yaml", ".yml", ".toml", ".log", ".rpt"},
    "source": {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".css", ".sh", ".bash", ".lua", ".blend", ".aseprite", ".otio"},
}
DIRECT_KINDS = {"image", "audio", "video", "html", "pdf", "text"}
DIRECT_SOURCE_EXTENSIONS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".css", ".sh", ".bash", ".lua"}

MIME_OVERRIDES = {
    ".svg": "image/svg+xml",
    ".md": "text/markdown; charset=utf-8",
    ".mdx": "text/plain; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".wasm": "application/wasm",
}


def presentation_kind(path: str) -> str:
    """Return a UI dispatch hint, never a preservation format identity."""
    ext = PurePosixPath(path).suffix.lower()
    for kind, extensions in PRESENTATION_KIND_EXTENSIONS.items():
        if ext in extensions:
            return kind
    return "other"


def _score(path: str, kind: str, *, launch: bool) -> int:
    p = path.lower()
    if launch:
        base = {"html": 1000, "video": 930, "audio": 900, "pdf": 860, "image": 820,
                "text": 700, "source": 640, "godot": 500, "cad": 420, "eda": 400, "other": 0}.get(kind, 0)
    else:
        base = {"image": 1000, "video": 920, "html": 860, "pdf": 760, "audio": 700,
                "cad": 360, "eda": 340, "godot": 320, "text": 180, "source": 120, "other": 0}.get(kind, 0)
    for token, delta in {
        "preview": 150, "thumbnail": 150, "artwork": 130, "render": 120, "output": 90,
        "carrier": 80, "final": 70, "review": 45, "desktop": 35, "index.html": 100,
        "main.tscn": 80, "project.godot": 70,
        "evidence": -160, "validation": -150, "verify": -150, "test": -140,
        "manifest": -130, "schema": -120, "source/": -70, "readme": -40,
    }.items():
        if token in p:
            base += delta
    ext = PurePosixPath(path).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        base += 80
    elif ext == ".gif":
        base += 70
    elif ext == ".svg":
        base += 50
    elif ext == ".mp4":
        base += 60
    elif ext == ".pdf":
        base += 30
    return base


def choose_carrier(carriers: list[dict], *, launch: bool) -> dict | None:
    if not carriers:
        return None
    eligible = [c for c in carriers if c["kind"] != "other"]
    if not eligible:
        return None
    return max(eligible, key=lambda c: (_score(c["relativePath"], c["kind"], launch=launch), -len(c["relativePath"]), c["relativePath"]))


def is_direct_carrier(carrier: dict | None) -> bool:
    if not carrier:
        return False
    if carrier["kind"] in DIRECT_KINDS:
        return True
    if carrier["kind"] == "source":
        return PurePosixPath(carrier["relativePath"]).suffix.lower() in DIRECT_SOURCE_EXTENSIONS
    return False


def _run_git(repo: str, args: list[str], *, binary: bool = False) -> bytes | str:
    proc = subprocess.run(["/usr/bin/git", "-C", repo, *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")


def git_tree(repo: str, revision: str, source_path: str) -> tuple[str, list[dict]]:
    raw = _run_git(repo, ["ls-tree", "-r", "-l", "-z", revision, "--", source_path], binary=True)
    entries: list[dict] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path_b = record.split(b"\t", 1)
        mode_b, type_b, oid_b, size_b = meta.split(b" ", 3)
        path = path_b.decode("utf-8", "surrogateescape")
        size_text = size_b.decode("ascii", "replace").strip()
        size = int(size_text) if size_text.isdigit() else None
        entries.append({"path": path, "mode": mode_b.decode(), "type": type_b.decode(), "objectId": oid_b.decode(), "size": size})
    if not entries:
        raise RuntimeError(f"no exact Git tree entries for {repo}@{revision}:{source_path}")
    is_single_file = len(entries) == 1 and entries[0]["path"] == source_path
    base = str(PurePosixPath(source_path).parent) if is_single_file else source_path.rstrip("/")
    if base == ".":
        base = ""
    carriers: list[dict] = []
    for entry in entries:
        path = entry["path"]
        rel = str(PurePosixPath(path).relative_to(PurePosixPath(base))) if base else path
        carriers.append({
            "relativePath": rel,
            "gitPath": path,
            "objectId": entry["objectId"],
            "size": entry["size"],
            "kind": presentation_kind(path),
        })
    return base, carriers


def canonical_digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _psql_json_lines(sql: str, *, socket: str, port: int, database: str) -> list[dict]:
    cmd = ["/usr/bin/runuser", "-u", "postgres", "--", "/usr/bin/psql", "-h", socket, "-p", str(port), "-d", database, "-At", "-c", sql]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip())
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def archive_from_postgres(*, socket: str, port: int, database: str) -> dict:
    works = _psql_json_lines(
        "SELECT row_to_json(x) FROM (SELECT work_id,title,owner,room,status,source_repo,source_revision,source_path,featured,series,evidence_level,physical_standing,human_standing,source_kind FROM creative_archive.works ORDER BY owner,title,work_id) x;",
        socket=socket, port=port, database=database)
    relations = _psql_json_lines(
        "SELECT row_to_json(x) FROM (SELECT child_work_id,parent_work_id,relation_type,evidence_summary FROM creative_archive.work_relations ORDER BY child_work_id,parent_work_id,relation_type) x;",
        socket=socket, port=port, database=database)
    findings = _psql_json_lines(
        "SELECT row_to_json(x) FROM (SELECT owner,source_path,evidence_revision,disposition,canonical_work_id,evidence_summary FROM creative_archive.reverse_census_findings WHERE run_id='reverse-source-complete-r1-20260911' ORDER BY owner,source_path) x;",
        socket=socket, port=port, database=database)
    manifest_rows = _psql_json_lines(
        "SELECT payload_text::json FROM creative_archive.source_snapshots WHERE snapshot_id='creative-archive-source-complete-r1-20260911';",
        socket=socket, port=port, database=database)
    if len(manifest_rows) != 1:
        raise RuntimeError("expected exactly one creative archive source-complete manifest")
    return {"manifest": manifest_rows[0], "works": works, "relations": relations, "reverseCensusFindings": findings}


def load_archive(args: argparse.Namespace) -> dict:
    if args.postgres:
        return archive_from_postgres(socket=args.pg_socket, port=args.pg_port, database=args.database)
    with open(args.archive_json, encoding="utf-8") as fh:
        return json.load(fh)


def _project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def load_derived_previews(path: str | Path | None) -> dict[str, dict]:
    if not path:
        return {}
    manifest_path = _project_path(path)
    if not manifest_path.exists():
        return {}
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.creative-library.derived-preview-manifest":
        raise RuntimeError("unexpected derived preview manifest kind/schema")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("derived preview manifest rows must be an array")
    root = DERIVED_ROOT.resolve()
    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("derived preview row must be an object")
        work_id = str(row.get("workId") or "")
        relative = str(row.get("path") or "")
        expected = str(row.get("sha256") or "")
        media_type = str(row.get("mediaType") or "")
        standing = str(row.get("standing") or "")
        receipt = str(row.get("provenanceReceipt") or "")
        if not work_id or work_id in result:
            raise RuntimeError(f"missing or duplicate derived preview work id: {work_id!r}")
        if not expected.startswith("sha256:") or len(expected) != 71:
            raise RuntimeError(f"invalid derived preview digest for {work_id}")
        if not media_type.startswith("image/"):
            raise RuntimeError(f"derived preview must be an image for {work_id}")
        candidate = _project_path(relative).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise RuntimeError(f"derived preview path escapes or is missing for {work_id}: {relative}")
        actual = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"derived preview digest mismatch for {work_id}: expected {expected}, observed {actual}")
        result[work_id] = {
            "path": relative, "sha256": expected, "mediaType": media_type,
            "standing": standing, "provenanceReceipt": receipt,
        }
    return result


def build_catalog(archive: dict, derived_previews: dict[str, dict] | None = None) -> dict:
    derived_previews = derived_previews or {}
    result_works: list[dict] = []
    total_carriers = 0
    direct_preview_works = 0
    for source in archive["works"]:
        repo = source.get("source_repo")
        revision = source.get("source_revision")
        source_path = source.get("source_path")
        if not (repo and revision and source_path):
            raise RuntimeError(f"work lacks exact source identity: {source.get('work_id')}")
        source_base, carriers = git_tree(repo, revision, source_path)
        total_carriers += len(carriers)
        modalities = sorted({c["kind"] for c in carriers if c["kind"] not in {"other", "source"}})
        hero = choose_carrier(carriers, launch=False)
        launch = choose_carrier(carriers, launch=True)
        if any(is_direct_carrier(c) for c in carriers):
            direct_preview_works += 1
        tree_digest = canonical_digest([(c["gitPath"], c["objectId"], c["size"]) for c in carriers])
        result_works.append({
            "workId": source["work_id"], "title": source["title"], "owner": source["owner"],
            "room": source.get("room"), "status": source.get("status"), "series": source.get("series"),
            "sourceRepo": repo, "sourceRevision": revision, "sourcePath": source_path,
            "sourceBase": source_base, "sourceTreeDigest": tree_digest,
            "featured": bool(source.get("featured")), "evidenceLevel": source.get("evidence_level"),
            "physicalStanding": source.get("physical_standing"), "humanStanding": source.get("human_standing"),
            "sourceKind": source.get("source_kind"), "modalities": modalities,
            "carrierCount": len(carriers), "heroCarrier": hero, "launchCarrier": launch,
            "derivedPreview": derived_previews.get(source["work_id"]), "carriers": carriers,
        })
    result_works.sort(key=lambda w: (w["owner"], w["title"].casefold(), w["workId"]))
    unknown_derived = sorted(set(derived_previews) - {w["workId"] for w in result_works})
    if unknown_derived:
        raise RuntimeError("derived preview references unknown work(s): " + ", ".join(unknown_derived))
    catalog_core = {
        "schemaVersion": SCHEMA_VERSION,
        "archiveStanding": archive.get("manifest", {}).get("standing", "UNKNOWN"),
        "archiveManifest": archive.get("manifest", {}),
        "works": result_works,
        "relations": archive.get("relations", []),
        "summary": {
            "workCount": len(result_works), "carrierCount": total_carriers,
            "directPreviewWorks": direct_preview_works, "derivedPreviewCount": len(derived_previews),
            "relationCount": len(archive.get("relations", [])),
        },
    }
    catalog_core["catalogDigest"] = canonical_digest(catalog_core)
    return catalog_core


def write_atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def safe_relative_path(value: str) -> str:
    if "\x00" in value:
        raise ValueError("NUL in path")
    raw_parts = value.split("/")
    if not value or value.startswith("/") or any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("unsafe relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in {"", ".", ".."} for part in p.parts):
        raise ValueError("unsafe relative path")
    return str(p)


def parse_range(header: str | None, size: int) -> tuple[int, int] | None:
    if not header:
        return None
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
    if not m:
        raise ValueError("unsupported byte range")
    a, b = m.groups()
    if not a and not b:
        raise ValueError("empty byte range")
    if not a:
        count = int(b)
        if count <= 0:
            raise ValueError("invalid suffix range")
        start = max(0, size - count)
        return start, size - 1
    start = int(a)
    end = int(b) if b else size - 1
    if start >= size or start < 0 or end < start:
        raise ValueError("unsatisfiable byte range")
    return start, min(end, size - 1)


class LibraryServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], catalog: dict):
        super().__init__(address, LibraryHandler)
        self.catalog = catalog
        self.work_by_id = {w["workId"]: w for w in catalog["works"]}
        self.path_maps = {w["workId"]: {c["relativePath"]: c for c in w["carriers"]} for w in catalog["works"]}
        self.derived_by_id = {w["workId"]: w["derivedPreview"] for w in catalog["works"] if w.get("derivedPreview")}


class LibraryHandler(BaseHTTPRequestHandler):
    server: LibraryServer

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("creative-library: " + (fmt % args) + "\n")

    def _headers(self, status: int, content_type: str, length: int | None = None, *, etag: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        if length is not None:
            self.send_header("Content-Length", str(length))
        if etag:
            self.send_header("ETag", f'"{etag}"')
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        else:
            self.send_header("Cache-Control", "no-store")

    def _send_bytes(self, body: bytes, content_type: str, *, status: int = 200, etag: str | None = None, extra: dict[str, str] | None = None, head_only: bool = False) -> None:
        self._headers(status, content_type, len(body), etag=etag)
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _send_json(self, obj: object, *, head_only: bool = False) -> None:
        self._send_bytes(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), "application/json; charset=utf-8", head_only=head_only)

    def _error(self, status: int, message: str, *, head_only: bool = False) -> None:
        self._send_bytes((message + "\n").encode(), "text/plain; charset=utf-8", status=status, head_only=head_only)

    def _serve_static(self, name: str, *, head_only: bool) -> None:
        path = WEB_ROOT / name
        if not path.is_file():
            self._error(404, "not found", head_only=head_only)
            return
        body = path.read_bytes()
        mime = MIME_OVERRIDES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if mime.startswith("text/") and "charset=" not in mime:
            mime += "; charset=utf-8"
        self._send_bytes(body, mime, etag=hashlib.sha256(body).hexdigest(), head_only=head_only)

    def _serve_raw(self, request_path: str, *, head_only: bool) -> None:
        rest = request_path[len("/raw/"):]
        if "/" not in rest:
            self._error(400, "raw path requires work id and carrier path", head_only=head_only)
            return
        work_part, rel_part = rest.split("/", 1)
        work_id = unquote(work_part)
        try:
            rel = safe_relative_path(unquote(rel_part))
        except ValueError:
            self._error(400, "unsafe carrier path", head_only=head_only)
            return
        work = self.server.work_by_id.get(work_id)
        carrier = self.server.path_maps.get(work_id, {}).get(rel)
        if not work or not carrier:
            self._error(404, "carrier is not in the frozen work tree", head_only=head_only)
            return
        body = _run_git(work["sourceRepo"], ["cat-file", "blob", f"{work['sourceRevision']}:{carrier['gitPath']}"], binary=True)
        assert isinstance(body, bytes)
        if hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest() != carrier["objectId"]:
            self._error(409, "Git blob identity mismatch", head_only=head_only)
            return
        ext = PurePosixPath(carrier["gitPath"]).suffix.lower()
        mime = MIME_OVERRIDES.get(ext) or mimetypes.guess_type(carrier["gitPath"])[0] or "application/octet-stream"
        if mime.startswith("text/") and "charset=" not in mime:
            mime += "; charset=utf-8"
        extra = {"Accept-Ranges": "bytes"}
        if carrier["kind"] == "html":
            extra["Content-Security-Policy"] = "sandbox allow-scripts; default-src 'self' data: blob:; connect-src 'none'; form-action 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"
        try:
            byte_range = parse_range(self.headers.get("Range"), len(body))
        except ValueError:
            self._headers(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, mime, 0, etag=carrier["objectId"])
            self.send_header("Content-Range", f"bytes */{len(body)}")
            self.end_headers()
            return
        if byte_range:
            start, end = byte_range
            piece = body[start:end + 1]
            extra["Content-Range"] = f"bytes {start}-{end}/{len(body)}"
            self._send_bytes(piece, mime, status=HTTPStatus.PARTIAL_CONTENT, etag=carrier["objectId"], extra=extra, head_only=head_only)
        else:
            self._send_bytes(body, mime, etag=carrier["objectId"], extra=extra, head_only=head_only)

    def _serve_derived(self, request_path: str, *, head_only: bool) -> None:
        encoded = request_path[len("/derived/"):]
        if not encoded or "/" in encoded:
            self._error(400, "derived path requires exactly one work id", head_only=head_only)
            return
        work_id = unquote(encoded)
        preview = self.server.derived_by_id.get(work_id)
        if not preview:
            self._error(404, "no derived preview for work", head_only=head_only)
            return
        candidate = _project_path(preview["path"]).resolve()
        if not candidate.is_relative_to(DERIVED_ROOT.resolve()) or not candidate.is_file():
            self._error(409, "derived preview path is unavailable", head_only=head_only)
            return
        body = candidate.read_bytes()
        actual = "sha256:" + hashlib.sha256(body).hexdigest()
        if actual != preview["sha256"]:
            self._error(409, "derived preview digest mismatch", head_only=head_only)
            return
        extra: dict[str, str] = {"X-Ordivon-Preview-Standing": preview["standing"]}
        if preview["mediaType"] == "image/svg+xml":
            extra["Content-Security-Policy"] = "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:"
        self._send_bytes(body, preview["mediaType"], etag=actual.removeprefix("sha256:"), extra=extra, head_only=head_only)

    def _dispatch(self, *, head_only: bool) -> None:
        path = urlsplit(self.path).path
        if path == "/api/catalog":
            self._send_json(self.server.catalog, head_only=head_only)
        elif path == "/api/health":
            self._send_json({"status": "ok", "catalogDigest": self.server.catalog["catalogDigest"], "workCount": len(self.server.catalog["works"])}, head_only=head_only)
        elif path.startswith("/raw/"):
            self._serve_raw(path, head_only=head_only)
        elif path.startswith("/derived/"):
            self._serve_derived(path, head_only=head_only)
        elif path in {"/", "/index.html"}:
            self._serve_static("index.html", head_only=head_only)
        elif path == "/app.js":
            self._serve_static("app.js", head_only=head_only)
        elif path == "/styles.css":
            self._serve_static("styles.css", head_only=head_only)
        else:
            self._error(404, "not found", head_only=head_only)

    def do_GET(self) -> None:
        self._dispatch(head_only=False)

    def do_HEAD(self) -> None:
        self._dispatch(head_only=True)


def cmd_build(args: argparse.Namespace) -> int:
    archive = load_archive(args)
    derived_previews = load_derived_previews(args.derived_manifest)
    catalog = build_catalog(archive, derived_previews)
    write_atomic_json(Path(args.output), catalog)
    print(json.dumps({"output": args.output, "catalogDigest": catalog["catalogDigest"], **catalog["summary"]}, ensure_ascii=False))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    expected = catalog.get("catalogDigest")
    test = dict(catalog)
    test.pop("catalogDigest", None)
    actual = canonical_digest(test)
    if expected != actual:
        raise RuntimeError(f"catalog digest mismatch: expected {expected}, recomputed {actual}")
    server = LibraryServer((args.bind, args.port), catalog)
    print(f"Creative Library: http://{args.bind}:{server.server_port}/  works={len(catalog['works'])} digest={expected}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build and serve the Ordivon Creative Library")
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="compile a carrier-aware catalog")
    b.add_argument("--archive-json", default=str(DEFAULT_ARCHIVE_JSON))
    b.add_argument("--postgres", action="store_true", help="read current creative_archive through psql instead of the frozen JSON export")
    b.add_argument("--pg-socket", default="/var/lib/postgres/ordivon-data-r5-pg-14550-v4")
    b.add_argument("--pg-port", type=int, default=55434)
    b.add_argument("--database", default="ordivon_assets")
    b.add_argument("--derived-manifest", default=str(DEFAULT_DERIVED_MANIFEST), help="optional digest-bound derived-preview manifest")
    b.add_argument("--output", default=str(DEFAULT_CATALOG))
    b.set_defaults(func=cmd_build)
    s = sub.add_parser("serve", help="serve the local read-only gallery")
    s.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    s.add_argument("--bind", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
