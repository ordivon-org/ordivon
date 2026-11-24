"""Independent parsing, Git source identity and native PostgreSQL behavior."""

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "catalogs/capabilities/ele/studies.py"
# Load the exact source-local CLI and its sibling pure relation extractor.
sys.path.insert(0, str(ENTRY.parent))
SPEC = importlib.util.spec_from_file_location("ele_studies", ENTRY)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_markdown_sections_preserve_source_and_hierarchy() -> None:
    fence = chr(96) * 3
    body = "# A\nIntro\n" + fence + "python\n# not a heading\n" + fence
    body += "\n## B\nBody\n### C\nDeep\n## D\nLast\n"
    sections = MODULE.markdown_sections(body)
    assert [section.heading for section in sections] == ["A", "B", "C", "D"]
    assert [section.path for section in sections] == [
        ("A",),
        ("A", "B"),
        ("A", "B", "C"),
        ("A", "D"),
    ]
    assert "".join(section.body for section in sections) == body
    assert sections[2].start_line < sections[2].end_line


def test_json_evidence_preserves_observation_identity() -> None:
    body = json.dumps(
        {
            "standing": "DISCOVERY_ONLY",
            "observations": [
                {
                    "upstream": {"repository": "https://github.com/sample/a"},
                    "result": "UNKNOWN",
                },
                {
                    "upstream": {"repository": "https://github.com/sample/b"},
                    "result": "REFERENCE_ONLY",
                },
            ],
        }
    )
    sections = MODULE.json_sections(body)
    assert len(sections) == 3
    assert "sample/a" in sections[1].heading
    assert "sample/b" in sections[2].heading
    assert json.loads(sections[1].body)["result"] == "UNKNOWN"


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def commit(root: Path) -> str:
    git(root, "add", "-A")
    git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    return git(root, "rev-parse", "HEAD").decode().strip()


def source_file(root: Path, path: str, content: str) -> Path:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def test_source_identity_distinguishes_analysis_and_acceptance(tmp_path: Path) -> None:
    provider = tmp_path / "catalogs/capabilities/providers" / "sample.md"
    analysis = tmp_path / "catalogs/knowledge/evidence/analysis" / "same.json"
    acceptance = tmp_path / "catalogs/knowledge/evidence/acceptance" / "same.json"
    for path, content in (
        (provider, "# Provider: Sample\n\nStudy\n"),
        (analysis, '{"kind":"analysis"}\n'),
        (acceptance, '{"kind":"acceptance"}\n'),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(tmp_path, "init", "-q")
    commit(tmp_path)
    studies = MODULE.capture_source(tmp_path).studies
    assert {study.study_id for study in studies} == {
        "provider:sample",
        "research_evidence:analysis/same",
        "research_evidence:acceptance/same",
    }
    assert (
        next(study for study in studies if study.study_id == "provider:sample").sha256
        == hashlib.sha256(provider.read_bytes()).hexdigest()
    )


def test_source_cut_excludes_dirty_staged_untracked_and_symlink_inputs(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    provider_path = "catalogs/capabilities/providers/sample.md"
    provider = source_file(tmp_path, provider_path, "# Original\n")
    target_path = "catalogs/capabilities/providers/target.md"
    target = source_file(tmp_path, target_path, "# Target\n")
    alias = provider.with_name("alias.md")
    alias.symlink_to(target.name)
    revision = commit(tmp_path)
    provider.write_text("# Staged\n")
    git(tmp_path, "add", provider_path)
    provider.write_text("# Transient\n")
    target.unlink()
    source_file(tmp_path, "catalogs/capabilities/providers/untracked.md", "# Untracked\n")
    corpus = MODULE.capture_source(tmp_path)
    assert corpus.revision == revision
    assert {s.study_id for s in corpus.studies} == {"provider:sample", "provider:target"}
    for study in corpus.studies:
        expected = git(tmp_path, "show", f"{revision}:{study.source_path}")
        assert study.content.encode("utf-8") == expected
        assert study.sha256 == hashlib.sha256(expected).hexdigest()


def test_head_change_after_freeze_cannot_mix_studies_or_reference_membership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    git(tmp_path, "init", "-q")
    first = "catalogs/capabilities/providers/sample.md"
    old = "catalogs/capabilities/ele/old.txt"
    new = "catalogs/capabilities/ele/new.txt"
    body = f"# Original\n[old]({old}) [new]({new})\n"
    provider = source_file(tmp_path, first, body)
    existing = source_file(tmp_path, old, "old")
    revision = commit(tmp_path)
    native = MODULE.git_bytes

    def change_after_freeze(root, *args):
        if args[0] == "ls-tree":
            provider.write_text("# Changed\n")
            existing.unlink()
            source_file(tmp_path, new, "new")
            commit(tmp_path)
        return native(root, *args)

    monkeypatch.setattr(MODULE, "git_bytes", change_after_freeze)
    corpus = MODULE.capture_source(tmp_path)
    assert corpus.revision == revision
    assert git(tmp_path, "rev-parse", "HEAD").decode().strip() != revision
    assert corpus.studies[0].content == body
    assert [ref.target for ref in corpus.references["provider:sample"]] == [old]


def test_local_git_replace_ref_cannot_substitute_committed_blob(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    path = "catalogs/capabilities/providers/sample.md"
    provider = source_file(tmp_path, path, "# Original\n")
    revision = commit(tmp_path)
    old_blob = git(tmp_path, "rev-parse", f"{revision}:{path}").decode().strip()
    provider.write_text("# Replacement\n", encoding="utf-8")
    replacement = git(tmp_path, "hash-object", "-w", path).decode().strip()
    git(tmp_path, "replace", old_blob, replacement)
    assert git(tmp_path, "cat-file", "blob", old_blob) == b"# Replacement\n"
    corpus = MODULE.capture_source(tmp_path)
    assert corpus.revision == revision
    assert corpus.studies[0].content == "# Original\n"
    assert corpus.studies[0].sha256 == hashlib.sha256(b"# Original\n").hexdigest()


def test_native_pg_import_replay_retire_and_exact_cut_readback(tmp_path: Path, monkeypatch) -> None:
    # Explicit scratch-only test. Never read the operator's ordinary ELE DSN.
    dsn = os.getenv("ORDIVON_ELE_TEST_DSN")
    if not dsn:
        pytest.skip("requires a fresh disposable PostgreSQL ele_fixture database")
    monkeypatch.setenv("ORDIVON_ELE_PG_DSN", dsn)
    with MODULE.connect() as conn:
        assert conn.execute("SELECT current_database()").fetchone()[0] == "ele_fixture"
        assert conn.execute("SELECT to_regnamespace('ele') IS NULL").fetchone()[0]
    git(tmp_path, "init", "-q")
    a = source_file(tmp_path, "catalogs/capabilities/providers/a.md", "# A\n## Child\n")
    b = source_file(tmp_path, "catalogs/capabilities/providers/b.md", "# B\n")
    revision = commit(tmp_path)
    corpus = MODULE.capture_source(tmp_path)
    a.write_text("# Uncommitted\n")
    first = MODULE.migrate(corpus)
    assert first["source_cut"] == revision
    assert (first["current_studies"], first["current_sections"], first["retained_versions"]) == (
        2,
        3,
        2,
    )
    assert (first["new_versions"], first["new_sections"]) == (2, 3)
    replay = MODULE.migrate(corpus)
    assert (replay["new_versions"], replay["new_sections"], replay["references_rebuilt"]) == (
        0,
        0,
        0,
    )

    # These use the actual CLI's run() consumer entry without consulting live
    # Git membership. The optional SQL filter must be typed even when absent.
    def query(action, *, kind=None, text=None, study_id=None):
        return MODULE.run(
            argparse.Namespace(action=action, kind=kind, query=text, id=study_id, limit=20)
        )

    with monkeypatch.context() as query_patch:

        def unexpected_source_read(*args, **kwargs):
            raise AssertionError("read-only projection must not recapture Git")

        query_patch.setattr(MODULE, "capture_source", unexpected_source_read)
        assert query("search", text="Child")["matches"]
    unfiltered = query("search", text="Child")
    assert [match["id"] for match in unfiltered["matches"]] == ["provider:a"]
    assert query("search", text="Child", kind="provider")["matches"] == unfiltered["matches"]
    assert query("search", text="Child", kind="lesson")["matches"] == []
    assert query("stats")["kinds"] == {"provider": 2}
    assert query("show", study_id="provider:a")["study"]["source_cut"] == revision
    assert query("links", study_id="provider:a")["outgoing"] == []
    with MODULE.connect() as conn:
        assert (
            conn.execute(
                "SELECT content FROM ele.current_studies WHERE study_id='provider:a'"
            ).fetchone()[0]
            == "# A\n## Child\n"
        )
        # Exact readback must reject a different claimed current cut, even
        # when the bytes and the section count still match.
        with pytest.raises(ValueError, match="PG readback failed"):
            with conn.transaction():
                conn.execute(
                    "UPDATE ele.study_heads SET source_cut=%s WHERE study_id='provider:a'",
                    ("0" * 40,),
                )
                MODULE.verify_cursor(conn.cursor(), corpus)
        MODULE.verify_cursor(conn.cursor(), corpus)
    a.write_text("# A\n## Child\n")
    b.unlink()
    next_revision = commit(tmp_path)
    retired = MODULE.migrate(MODULE.capture_source(tmp_path))
    assert retired["source_cut"] == next_revision
    assert (
        retired["current_studies"],
        retired["current_sections"],
        retired["retained_versions"],
    ) == (1, 2, 2)
    source_file(tmp_path, "catalogs/capabilities/providers/b.md", "# B\n")
    commit(tmp_path)
    restored = MODULE.migrate(MODULE.capture_source(tmp_path))
    assert (
        restored["current_studies"],
        restored["current_sections"],
        restored["retained_versions"],
        restored["new_versions"],
    ) == (2, 3, 2, 0)


def test_explicit_json_references_preserve_consumer_boundary() -> None:
    from relations import references_for

    content = json.dumps(
        {
            "source": {"upstream": {"repository": "https://github.com/demo/tool"}},
            "references": {
                "provider": "catalogs/capabilities/providers/worktrunk.md",
                "consumerSources": ["catalogs/capabilities/ele/example.rs"],
                "notAnInstalledProvider": "No production switch",
            },
        }
    )
    record = MODULE.Study(
        "candidate_evidence:demo",
        "a" * 64,
        "candidate_evidence",
        "catalogs/capabilities/evidence/demo.json",
        "demo",
        content,
        MODULE.json_sections(content),
    )
    refs = references_for(
        record,
        {"catalogs/capabilities/providers/worktrunk.md": "provider:worktrunk"},
        {
            "catalogs/capabilities/providers/worktrunk.md",
            "catalogs/capabilities/ele/example.rs",
        },
    )
    assert len(refs) == 3
    assert [ref.relation for ref in refs] == [
        "upstream_repository_reference",
        "git_source",
        "consumer_source_reference",
    ]
    assert refs[1].target_study_id == "provider:worktrunk"
    assert refs[2].locator == "$.references.consumerSources[0]"
    assert not any("installed" in ref.relation for ref in refs)


def test_markdown_links_do_not_convert_uncited_claims_into_edges() -> None:
    from relations import references_for

    body = (
        "# Project comparison\n"
        "Some discussions mention catalogs/capabilities/ele/example.rs outside a citation.\n"
        "Qualified source: [provider](../../capabilities/providers/worktrunk.md).\n"
        "Existing Git source path: \x60catalogs/capabilities/ele/example.rs\x60.\n"
        "Unsupported: [not present](not-real.md).\n"
    )
    record = MODULE.Study(
        "lesson:demo",
        "b" * 64,
        "lesson",
        "catalogs/knowledge/lessons/demo.md",
        "demo",
        body,
        MODULE.markdown_sections(body),
    )
    refs = references_for(
        record,
        {"catalogs/capabilities/providers/worktrunk.md": "provider:worktrunk"},
        {
            "catalogs/capabilities/providers/worktrunk.md",
            "catalogs/capabilities/ele/example.rs",
        },
    )
    assert len(refs) == 2
    assert refs[0].target == "catalogs/capabilities/providers/worktrunk.md"
    assert refs[0].target_study_id == "provider:worktrunk"
    assert refs[0].locator == "line:3"
    assert refs[1].target == "catalogs/capabilities/ele/example.rs"
    assert refs[1].locator == "line:4"
