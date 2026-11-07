"""PostgreSQL read model for source-bound Ordivon ELE project studies.

Git remains the authoring source. Imported records are dated research snapshots,
not executable-provider status, natural Owner decisions or formal LEGO admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from relations import Reference, all_references

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = Path(__file__).with_name("schema.sql")
SOURCES = (
    ("provider", "catalogs/capabilities/providers/*.md"),
    ("lesson", "catalogs/knowledge/lessons/*.md"),
    ("package", "catalogs/capabilities/packages/*.md"),
    ("candidate_evidence", "catalogs/capabilities/evidence/*.json"),
    ("knowledge_graph", "catalogs/knowledge/graphs/*.json"),
    ("research_evidence", "catalogs/knowledge/evidence/analysis/*.json"),
    ("research_evidence", "catalogs/knowledge/evidence/acceptance/*.json"),
    ("authority_map", "catalogs/capabilities/authority-map-r1.md"),
    ("research_package", "catalogs/capabilities/RESEARCH_CAPABILITY_PACKAGE_R1.md"),
    # Curated cross-Owner research, read-only projections; execution stays with the Owner.
    (
        "artifact_decomposition",
        "capabilities/artifact/docs/ARTIFACT_CAPABILITY_DECOMPOSITION_WAVE_A*.md",
    ),
    (
        "artifact_decomposition",
        "capabilities/artifact/docs/ARTIFACT_REDECOMPOSITION_R1.md",
    ),
    (
        "preservation_comparison",
        "capabilities/preservation/docs/creative-preservation-external-composition-r1.md",
    ),
    (
        "preservation_comparison",
        "capabilities/preservation/docs/creative-preservation-standards-migration-r8.md",
    ),
    (
        "finance_qualification",
        "domains/capital/docs/EXTERNAL_IMPLEMENTATION_QUALIFICATION_R1.md",
    ),
    (
        "finance_qualification",
        "domains/capital/docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md",
    ),
    (
        "research_qualification",
        "profiles/research/tool-qualification/TOOL_QUALIFICATION_R1.md",
    ),
    ("research_qualification", "profiles/research/tool-qualification/examples/*.json"),
    ("network_comparison", "platform/network/docs/DECISION_MATRIX.md"),
    (
        "harness_comparison",
        "services/harness/docs/BROWSER_DECISION_PROVIDER_DUEL_R1.md",
    ),
    ("harness_comparison", "services/harness/docs/LAYA_ARCHITECTURE_DUEL_R1.md"),
    ("harness_comparison", "services/harness/docs/BROWSER_CAPABILITY_ROUTER_R1.md"),
    ("media_research", "capabilities/media/research/expression/*.md"),
)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
FENCE = re.compile(r"^[ \t]*(" + chr(96) + r"{3,}|~{3,})")


@dataclass(frozen=True)
class Section:
    ordinal: int
    level: int
    path: tuple[str, ...]
    heading: str
    body: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Study:
    study_id: str
    sha256: str
    kind: str
    source_path: str
    title: str
    content: str
    sections: tuple[Section, ...]


def markdown_sections(content: str) -> tuple[Section, ...]:
    lines = content.splitlines(keepends=True)
    headings: list[tuple[int, int, str]] = []
    fenced: str | None = None
    for i, line in enumerate(lines):
        match = FENCE.match(line)
        if match:
            marker = match.group(1)[0]
            if fenced is None:
                fenced = marker
            elif fenced == marker:
                fenced = None
            continue
        if fenced is None and (heading := HEADING.match(line.strip())):
            headings.append(
                (i, len(heading.group(1)), heading.group(2).rstrip("# ").strip())
            )
    if not headings:
        return (Section(0, 0, (), "Document", content, 1, len(lines)),)
    sections: list[Section] = []
    ancestors: list[tuple[int, str]] = []
    if headings[0][0]:
        sections.append(
            Section(
                0,
                0,
                (),
                "Preamble",
                "".join(lines[: headings[0][0]]),
                1,
                headings[0][0],
            )
        )
    for index, (start, level, title) in enumerate(headings):
        while ancestors and ancestors[-1][0] >= level:
            ancestors.pop()
        ancestors.append((level, title))
        stop = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        sections.append(
            Section(
                len(sections),
                level,
                tuple(name for _, name in ancestors),
                title,
                "".join(lines[start:stop]),
                start + 1,
                stop,
            )
        )
    return tuple(sections)


def json_sections(content: str) -> tuple[Section, ...]:
    data = json.loads(content)
    if not isinstance(data, dict):
        return (Section(0, 0, (), "JSON", content, 0, 0),)
    sections: list[Section] = []
    for key, value in data.items():
        if key == "observations" and isinstance(value, list):
            for i, observation in enumerate(value):
                label = f"observations[{i}]"
                if isinstance(observation, dict):
                    upstream = observation.get("upstream")
                    if isinstance(upstream, dict) and isinstance(
                        upstream.get("repository"), str
                    ):
                        label += f": {upstream['repository']}"
                sections.append(
                    Section(
                        len(sections),
                        2,
                        ("observations", label),
                        label,
                        json.dumps(observation, ensure_ascii=False, indent=2),
                        0,
                        0,
                    )
                )
        else:
            sections.append(
                Section(
                    len(sections),
                    1,
                    (key,),
                    key,
                    json.dumps(value, ensure_ascii=False, indent=2),
                    0,
                    0,
                )
            )
    return tuple(sections)


def gather(root: Path = ROOT) -> list[Study]:
    studies: list[Study] = []
    seen: set[str] = set()
    for kind, pattern in SOURCES:
        for file in sorted(root.glob(pattern)):
            if not file.is_file() or file.is_symlink():
                continue
            study_id = (
                f"{kind}:{file.parent.name}/{file.stem}"
                if kind == "research_evidence"
                else f"{kind}:{file.stem}"
            )
            if study_id in seen:
                raise ValueError(f"ELE study ID collision: {study_id}")
            seen.add(study_id)
            raw = file.read_bytes()
            content = raw.decode("utf-8")
            parts = (
                json_sections(content)
                if file.suffix == ".json"
                else markdown_sections(content)
            )
            title = next((part.heading for part in parts if part.level == 1), file.stem)
            studies.append(
                Study(
                    study_id,
                    hashlib.sha256(raw).hexdigest(),
                    kind,
                    file.relative_to(root).as_posix(),
                    title,
                    content,
                    parts,
                )
            )
    return sorted(studies, key=lambda study: study.study_id)


def source_cut(root: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def verify_source_cut(studies: list[Study], root: Path = ROOT) -> None:
    """Require imported bytes to be the exact committed Git SourceCut.

    The two batched native Git reads prevent dirty or untracked analysis files
    from being attributed to a commit that never contained those bytes.
    """
    paths = [study.source_path for study in studies]
    objects = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=root,
        input="".join(f"HEAD:{path}\n" for path in paths),
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    working = subprocess.run(
        ["git", "hash-object", "--stdin-paths"],
        cwd=root,
        input="".join(f"{path}\n" for path in paths),
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    if len(objects) != len(paths) or len(working) != len(paths):
        raise ValueError("incomplete Git source identity readback")
    mismatched = [
        path
        for path, obj, hashed in zip(paths, objects, working, strict=True)
        if len(obj.split()) != 3 or obj.split()[1] != "blob" or obj.split()[0] != hashed
    ]
    if mismatched:
        raise ValueError(f"ELE source differs from Git HEAD: {mismatched[:8]}")
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            *(pattern for _, pattern in SOURCES),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    if status.stdout.strip():
        raise ValueError("ELE source paths contain uncommitted additions or deletions")


def connect() -> Any:
    dsn = os.getenv("ORDIVON_ELE_PG_DSN")
    if not dsn:
        raise SystemExit("ORDIVON_ELE_PG_DSN is required; ELE has no SQLite fallback")
    import psycopg

    return psycopg.connect(dsn, connect_timeout=8)


def verify_cursor(
    cur: Any, studies: list[Study], references: dict[str, tuple[Reference, ...]]
) -> dict[str, int]:
    expected = {
        s.study_id: (s.sha256, s.source_path, s.title, len(s.sections)) for s in studies
    }
    cur.execute(
        """SELECT h.study_id,h.sha256,v.source_path,v.title,v.content,count(s.ordinal)
           FROM ele.study_heads AS h
           JOIN ele.study_versions AS v
             ON v.study_id=h.study_id AND v.sha256=h.sha256
           LEFT JOIN ele.study_sections AS s
             ON s.study_id=h.study_id AND s.sha256=h.sha256
           WHERE h.present
           GROUP BY h.study_id,h.sha256,v.source_path,v.title,v.content"""
    )
    actual = {}
    corrupt: list[str] = []
    for study_id, digest, path, title, body, sections in cur.fetchall():
        actual[study_id] = (digest.strip(), path, title, sections)
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != digest.strip():
            corrupt.append(study_id)
    if expected != actual or corrupt:
        missing = sorted(expected.keys() - actual.keys())[:8]
        extra = sorted(actual.keys() - expected.keys())[:8]
        wrong = sorted(
            k for k in actual.keys() & expected.keys() if actual[k] != expected[k]
        )[:8]
        raise ValueError(
            f"ELE PG readback failed missing={missing} extra={extra} wrong={wrong} corrupt={corrupt[:8]}"
        )
    expected_sections = {
        (study.study_id, section.ordinal): (
            section.level,
            section.path,
            section.heading,
            section.body,
            section.start_line,
            section.end_line,
        )
        for study in studies
        for section in study.sections
    }
    cur.execute(
        """SELECT s.study_id,s.ordinal,s.heading_level,s.heading_path,
                  s.heading,s.body,s.start_line,s.end_line
           FROM ele.study_sections AS s
           JOIN ele.study_heads AS h
             ON h.study_id=s.study_id AND h.sha256=s.sha256
           WHERE h.present"""
    )
    actual_sections = {
        (sid, ordinal): (level, tuple(path), heading, body, start, end)
        for sid, ordinal, level, path, heading, body, start, end in cur.fetchall()
    }
    if expected_sections != actual_sections:
        missing = sorted(expected_sections.keys() - actual_sections.keys())[:5]
        wrong = sorted(
            key
            for key in expected_sections.keys() & actual_sections.keys()
            if expected_sections[key] != actual_sections[key]
        )[:5]
        raise ValueError(
            f"ELE PG section readback failed missing={missing}, changed={wrong}"
        )
    expected_refs = {
        (study.study_id, ref.ordinal): (
            ref.section_ordinal,
            ref.relation,
            ref.locator,
            ref.target,
            ref.target_study_id,
        )
        for study in studies
        for ref in references[study.study_id]
    }
    cur.execute(
        """SELECT r.study_id,r.ordinal,r.section_ordinal,r.relation,
                  r.locator,r.target,r.target_study_id
           FROM ele.study_references AS r
           JOIN ele.study_heads AS h
             ON h.study_id=r.study_id AND h.sha256=r.sha256
           WHERE h.present"""
    )
    actual_refs = {
        (sid, ordinal): (section, relation, locator, target, target_id)
        for sid, ordinal, section, relation, locator, target, target_id in cur.fetchall()
    }
    if actual_refs != expected_refs:
        missing = sorted(expected_refs.keys() - actual_refs.keys())[:5]
        wrong = sorted(
            key
            for key in expected_refs.keys() & actual_refs.keys()
            if expected_refs[key] != actual_refs[key]
        )[:5]
        raise ValueError(
            f"ELE PG source-reference readback mismatch missing={missing}, changed={wrong}"
        )
    cur.execute("SELECT count(*) FROM ele.study_versions")
    return {
        "current_studies": len(actual),
        "current_sections": sum(value[1] for value in actual.values()),
        "current_references": len(actual_refs),
        "retained_versions": cur.fetchone()[0],
    }


def migrate(
    studies: list[Study],
    revision: str,
    references: dict[str, tuple[Reference, ...]],
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("exact Git source revision required")
    if not studies:
        raise ValueError("empty corpus cannot replace active study catalog")
    with connect() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA.read_text(encoding="utf-8"))
        cur.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            ("ordivon-ele-project-study-v1",),
        )
        added = 0
        sections_added = 0
        references_rebuilt = 0
        for study in studies:
            cur.execute(
                """INSERT INTO ele.study_versions
                   (study_id,sha256,kind,source_path,source_cut,title,content)
                   VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (
                    study.study_id,
                    study.sha256,
                    study.kind,
                    study.source_path,
                    revision,
                    study.title,
                    study.content,
                ),
            )
            added += cur.rowcount
            for section in study.sections:
                cur.execute(
                    """INSERT INTO ele.study_sections
                       (study_id,sha256,ordinal,heading_level,heading_path,heading,body,start_line,end_line)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (
                        study.study_id,
                        study.sha256,
                        section.ordinal,
                        section.level,
                        list(section.path),
                        section.heading,
                        section.body,
                        section.start_line,
                        section.end_line,
                    ),
                )
                sections_added += cur.rowcount
            cur.execute(
                """SELECT ordinal,section_ordinal,relation,locator,target,target_study_id
                   FROM ele.study_references
                   WHERE study_id=%s AND sha256=%s ORDER BY ordinal""",
                (study.study_id, study.sha256),
            )
            expected = [
                (
                    ref.ordinal,
                    ref.section_ordinal,
                    ref.relation,
                    ref.locator,
                    ref.target,
                    ref.target_study_id,
                )
                for ref in references[study.study_id]
            ]
            if cur.fetchall() != expected:
                cur.execute(
                    "DELETE FROM ele.study_references WHERE study_id=%s AND sha256=%s",
                    (study.study_id, study.sha256),
                )
                for ref in references[study.study_id]:
                    cur.execute(
                        """INSERT INTO ele.study_references
                           (study_id,sha256,ordinal,section_ordinal,relation,
                            locator,target,target_study_id)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            ref.study_id,
                            ref.sha256,
                            ref.ordinal,
                            ref.section_ordinal,
                            ref.relation,
                            ref.locator,
                            ref.target,
                            ref.target_study_id,
                        ),
                    )
                references_rebuilt += len(expected)
            cur.execute(
                """INSERT INTO ele.study_heads (study_id,sha256,source_cut,present)
                   VALUES (%s,%s,%s,true)
                   ON CONFLICT (study_id) DO UPDATE
                   SET sha256=EXCLUDED.sha256,source_cut=EXCLUDED.source_cut,
                       present=true,last_imported_at=now()""",
                (study.study_id, study.sha256, revision),
            )
        cur.execute(
            "UPDATE ele.study_heads SET present=false WHERE present AND source_cut <> %s",
            (revision,),
        )
        report = verify_cursor(cur, studies, references)
        report.update(
            new_versions=added,
            new_sections=sections_added,
            references_rebuilt=references_rebuilt,
            source_cut=revision,
        )
    return report


def run(args: argparse.Namespace) -> dict[str, Any]:
    studies = gather()
    references = all_references(studies, ROOT)
    if args.action == "plan":
        counts: dict[str, int] = {}
        for study in studies:
            counts[study.kind] = counts.get(study.kind, 0) + 1
        return {
            "source_cut": source_cut(),
            "studies": len(studies),
            "sections": sum(len(study.sections) for study in studies),
            "references": sum(len(group) for group in references.values()),
            "kinds": counts,
        }
    if args.action == "migrate":
        verify_source_cut(studies)
        return migrate(studies, source_cut(), references)
    with connect() as conn, conn.cursor() as cur:
        if args.action == "verify":
            return verify_cursor(cur, studies, references)
        if args.action == "stats":
            cur.execute(
                "SELECT kind,count(*) FROM ele.current_studies GROUP BY kind ORDER BY kind"
            )
            by_kind = dict(cur.fetchall())
            cur.execute(
                """SELECT count(*) FROM ele.study_references AS r
                   JOIN ele.study_heads AS h
                     ON h.study_id=r.study_id AND h.sha256=r.sha256
                   WHERE h.present"""
            )
            return {"kinds": by_kind, "references": cur.fetchone()[0]}
        if args.action == "links":
            if not args.id:
                raise SystemExit("--id is required")
            cur.execute(
                """SELECT source_path,last_observed_source_cut,sha256
                   FROM ele.current_studies WHERE study_id=%s""",
                (args.id,),
            )
            source = cur.fetchone()
            if not source:
                raise SystemExit(f"study missing: {args.id}")
            cur.execute(
                """SELECT r.relation,r.locator,r.target,r.target_study_id,
                          r.section_ordinal
                   FROM ele.study_references AS r
                   JOIN ele.study_heads AS h
                     ON h.study_id=r.study_id AND h.sha256=r.sha256
                   WHERE h.present AND r.study_id=%s ORDER BY r.ordinal""",
                (args.id,),
            )
            outgoing = [
                {
                    "relation": rel,
                    "locator": loc,
                    "target": target,
                    "study_id": sid,
                    "section": section,
                }
                for rel, loc, target, sid, section in cur.fetchall()
            ]
            cur.execute(
                """SELECT r.study_id,r.relation,r.locator,r.section_ordinal
                   FROM ele.study_references AS r
                   JOIN ele.study_heads AS h
                     ON h.study_id=r.study_id AND h.sha256=r.sha256
                   WHERE h.present AND r.target=%s
                   ORDER BY r.study_id,r.ordinal""",
                (source[0],),
            )
            incoming = [
                {"study_id": sid, "relation": rel, "locator": loc, "section": section}
                for sid, rel, loc, section in cur.fetchall()
            ]
            return {
                "id": args.id,
                "source_path": source[0],
                "source_cut": source[1],
                "sha256": source[2],
                "outgoing": outgoing,
                "incoming": incoming,
            }
        if args.action == "show":
            if not args.id:
                raise SystemExit("--id is required")
            cur.execute(
                """SELECT study_id,kind,source_path,sha256,last_observed_source_cut,title
                   FROM ele.current_studies WHERE study_id=%s""",
                (args.id,),
            )
            row = cur.fetchone()
            if row is None:
                raise SystemExit(f"study missing: {args.id}")
            cur.execute(
                """SELECT s.heading_level,s.heading_path,s.heading,s.start_line,s.end_line,s.body
                   FROM ele.study_sections AS s
                   JOIN ele.study_heads AS h ON h.study_id=s.study_id AND h.sha256=s.sha256
                   WHERE h.present AND s.study_id=%s ORDER BY s.ordinal""",
                (args.id,),
            )
            sections = [
                {
                    "level": level,
                    "path": path,
                    "heading": heading,
                    "start_line": first,
                    "end_line": last,
                    "body": body,
                }
                for level, path, heading, first, last, body in cur.fetchall()
            ]
            return {
                "study": dict(
                    zip(
                        ("id", "kind", "source_path", "sha256", "source_cut", "title"),
                        row,
                        strict=True,
                    )
                ),
                "sections": sections,
            }
        if args.action == "search":
            if not args.query:
                raise SystemExit("--query is required")
            cur.execute(
                """SELECT s.study_id,v.kind,v.source_path,s.heading_path,left(s.body,220)
                   FROM ele.study_heads AS h
                   JOIN ele.study_sections AS s
                     ON s.study_id=h.study_id AND s.sha256=h.sha256
                   JOIN ele.study_versions AS v
                     ON v.study_id=h.study_id AND v.sha256=h.sha256
                   WHERE h.present AND (%s IS NULL OR v.kind=%s) AND
                     (to_tsvector('simple',s.body) @@ plainto_tsquery('simple',%s)
                      OR s.body ILIKE ('%%' || %s || '%%'))
                   ORDER BY s.study_id,s.ordinal LIMIT %s""",
                (args.kind, args.kind, args.query, args.query, args.limit),
            )
            return {
                "query": args.query,
                "kind": args.kind,
                "matches": [
                    {
                        "id": sid,
                        "kind": kind,
                        "source_path": path,
                        "headings": heading,
                        "excerpt": excerpt,
                    }
                    for sid, kind, path, heading, excerpt in cur.fetchall()
                ],
            }
    raise SystemExit("unknown action")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ordivon ELE project study PG projection"
    )
    parser.add_argument(
        "action",
        choices=("plan", "migrate", "verify", "stats", "show", "search", "links"),
    )
    parser.add_argument("--id")
    parser.add_argument("--query")
    parser.add_argument("--kind")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
