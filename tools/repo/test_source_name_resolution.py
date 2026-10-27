from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from source_name_resolution import resolve_source_name


def source_cut(rows):
    return {
        "truthRole": "SOURCE_NAVIGATION_NOT_OWNER_OR_LEGO_QUALIFICATION",
        "sourceRevision": "a" * 40,
        "sourceTree": "b" * 40,
        "ownerManifestIdentity": "100644:blob:" + "c" * 40,
        "classifierSourceIdentity": "100644:blob:" + "d" * 40,
        "entries": rows,
    }


def row(path, cell, label, owner, *, region=None, section=None):
    return {
        "path": path,
        "sourceIdentity": "100644:blob:" + ("a" * 40),
        "sourceCell": cell,
        "sourceCellDisplayName": label,
        "sourceSection": section,
        "sourceRegion": region,
        "semanticName": "Implementations" if owner else "Documentation",
        "verificationOwner": owner,
        "sourceCellRole": "UNQUALIFIED_NESTED_CELL",
        "sourceSectionRole": "UNQUALIFIED_SECTION",
        "sourceFileForm": "PYTHON_SOURCE_FILE",
        "classificationStanding": "REGISTERED_OWNER_SOURCE"
        if owner
        else "DECLARED_SOURCE_REGION",
    }


class SourceNameResolutionTests(unittest.TestCase):
    def setUp(self):
        self.cut = source_cut(
            [
                row(
                    "services/runtime/src/job.py",
                    "runtime/src/job",
                    "Common Tools",
                    "runtime",
                ),
                row(
                    "services/runtime/src/work.py",
                    "runtime/src/job",
                    "Common Tools",
                    "runtime",
                ),
                row(
                    "services/harness/src/bridge.py",
                    "harness/src/bridge",
                    "Common Tools",
                    "harness",
                ),
                row(
                    "services/gateway/src/route.py",
                    "gateway/src/route",
                    "Gateway Routing",
                    "gateway",
                ),
                row("docs/architecture/README.md", None, None, None, region="docs"),
            ]
        )

    def test_colliding_display_name_must_be_ambiguous(self):
        result = resolve_source_name(
            self.cut, name="Common Tools", field="sourceCellDisplayName"
        )
        self.assertEqual(result["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")
        self.assertEqual(result["candidateGroupCount"], 2)
        self.assertEqual(result["candidates"][1]["matchedPaths"], 2)
        self.assertFalse(result["semanticIdentityQualified"])
        self.assertFalse(result["physicalRenameAdmissible"])

    def test_explicit_scope_recovers_unique_group_without_guessing(self):
        result = resolve_source_name(
            self.cut,
            name="Common Tools",
            field="sourceCellDisplayName",
            scope_prefix="services/runtime/",
        )
        self.assertEqual(result["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
        self.assertEqual(result["candidateGroupCount"], 1)
        self.assertEqual(result["candidates"][0]["sourceGroup"], "runtime/src/job")
        self.assertEqual(result["candidates"][0]["matchedPaths"], 2)

    def test_source_cell_identity_excludes_similar_name(self):
        result = resolve_source_name(
            self.cut, name="runtime/src/job", field="sourceCell"
        )
        self.assertEqual(result["candidateGroupCount"], 1)
        self.assertEqual(
            result["candidates"][0]["sampleSourceObjects"][0]["path"],
            "services/runtime/src/job.py",
        )

    def test_same_owner_semantic_name_is_not_unique_across_many_cells(self):
        result = resolve_source_name(
            self.cut, name="Implementations", field="semanticName"
        )
        self.assertEqual(result["candidateGroupCount"], 3)
        self.assertEqual(result["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")

    def test_truncated_never_silently_selects_first(self):
        result = resolve_source_name(
            self.cut,
            name="Common Tools",
            field="sourceCellDisplayName",
            max_candidates=1,
        )
        self.assertTrue(result["truncated"])
        self.assertEqual(result["candidateGroupCount"], 2)
        self.assertEqual(result["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")

    def test_absent_label_fails_closed_no_implicit_fuzzy_matching(self):
        result = resolve_source_name(
            self.cut,
            name="Common Tool",
            field="sourceCellDisplayName",
        )
        self.assertEqual(result["standing"], "NOT_FOUND")
        self.assertEqual(result["candidateGroupCount"], 0)

    def test_navigation_only_region_never_becomes_approval_authority(self):
        result = resolve_source_name(self.cut, name="docs", field="sourceRegion")
        self.assertEqual(result["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
        self.assertEqual(
            result["candidates"][0]["classificationStanding"], "DECLARED_SOURCE_REGION"
        )
        self.assertFalse(result["proofReuseAdmissible"])

    def test_invalid_names_fields_and_source_cut_truth_are_rejected(self):
        for kwargs in (
            {"name": " Common Tools"},
            {"field": "approval"},
            {"scope_prefix": "../"},
            {"scope_prefix": "/"},
            {"scope_prefix": "services//runtime/"},
            {"max_candidates": True},
            {"max_candidates": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                resolve_source_name(
                    self.cut,
                    **(
                        {"name": "Common Tools", "field": "sourceCellDisplayName"}
                        | kwargs
                    ),
                )
        with self.assertRaises(ValueError):
            resolve_source_name(
                {"truthRole": "fake", "sourceRevision": "a"},
                name="Common Tools",
                field="sourceCellDisplayName",
            )

    def test_cli_on_real_git_source_cut(self):
        repo = Path(__file__).resolve().parents[2]
        cut = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        result = subprocess.run(
            [
                sys.executable,
                str(repo / "tools/repo/source_name_resolution.py"),
                "--source-cut",
                cut,
                "--repo",
                str(repo),
                "--name",
                "runtime",
                "--field",
                "verificationOwner",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["sourceRevision"], cut)
        self.assertGreater(output["candidateGroupCount"], 1)
        self.assertEqual(output["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")
        self.assertFalse(output["semanticIdentityQualified"])


if __name__ == "__main__":
    unittest.main()
