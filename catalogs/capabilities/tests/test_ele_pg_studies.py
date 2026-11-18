"""Tests only the two decision-changing parsing boundaries (not a mock PG)."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

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
    studies = MODULE.gather(tmp_path)
    assert {study.study_id for study in studies} == {
        "provider:sample",
        "research_evidence:analysis/same",
        "research_evidence:acceptance/same",
    }
    assert (
        next(study for study in studies if study.study_id == "provider:sample").sha256
        == hashlib.sha256(provider.read_bytes()).hexdigest()
    )


def test_source_cut_rejects_uncommitted_research_claim(tmp_path: Path) -> None:
    import subprocess

    import pytest

    provider = tmp_path / "catalogs/capabilities/providers" / "sample.md"
    provider.parent.mkdir(parents=True)
    provider.write_text("# Sample\nVersion A\n", encoding="utf-8")
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "catalogs/capabilities/providers/sample.md"],
        [
            "git",
            "-c",
            "user.name=Research",
            "-c",
            "user.email=research@localhost",
            "commit",
            "-q",
            "-m",
            "freeze source",
        ],
    ):
        subprocess.run(command, cwd=tmp_path, check=True, capture_output=True)
    MODULE.verify_source_cut(MODULE.gather(tmp_path), tmp_path)
    provider.write_text("# Sample\nVersion B not committed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from Git HEAD"):
        MODULE.verify_source_cut(MODULE.gather(tmp_path), tmp_path)


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
