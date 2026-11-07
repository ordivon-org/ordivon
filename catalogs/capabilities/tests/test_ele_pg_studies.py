"""Tests only the two decision-changing parsing boundaries (not a mock PG)."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "catalogs/capabilities/ele/studies.py"
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
