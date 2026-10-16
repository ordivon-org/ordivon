#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("information_census.py")
SPEC = importlib.util.spec_from_file_location("information_census", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InformationCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.census = MODULE.build_information_census("HEAD")

    def test_path_resolution_preserves_ambiguity(self) -> None:
        tracked = {
            ".github/workflows/ci.yml",
            "domains/capital/.github/workflows/ci.yml",
        }
        value = MODULE.resolve_source_path(
            "domains/capital/planning/lego-plan-r1.json",
            ".github/workflows/ci.yml",
            tracked,
            pointer="/nodes/0/files/0",
        )
        self.assertEqual(value["standing"], "AMBIGUOUS_EXACT")
        self.assertEqual(
            value["candidates"],
            [
                ".github/workflows/ci.yml",
                "domains/capital/.github/workflows/ci.yml",
            ],
        )

    def test_explicit_relative_path_is_not_reinterpreted_from_every_ancestor(
        self,
    ) -> None:
        tracked = {
            "README.md",
            "services/harness/README.md",
        }
        value = MODULE.resolve_source_path(
            "services/harness/docs/EXTRACTION.md",
            "../README.md",
            tracked,
            pointer="/reference",
        )
        self.assertEqual(value["standing"], "EXACT_UNIQUE")
        self.assertEqual(value["candidates"], ["services/harness/README.md"])

    def test_path_resolution_finds_unique_ancestor_relative_target(self) -> None:
        tracked = {
            "domains/capital/config/policy.json",
            "domains/capital/evidence/receipt.json",
        }
        value = MODULE.resolve_source_path(
            "domains/capital/evidence/receipt.json",
            "config/policy.json",
            tracked,
            pointer="/policy",
        )
        self.assertEqual(value["standing"], "EXACT_UNIQUE")
        self.assertEqual(value["candidates"], ["domains/capital/config/policy.json"])

    def test_git_revision_census_distinguishes_local_commit_from_missing_object(
        self,
    ) -> None:
        import subprocess

        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=MODULE.ROOT,
            text=True,
        ).strip()
        absent = "f" * 40
        exact, unresolved = MODULE._check_git_revisions({head, absent})
        self.assertEqual(exact, {head})
        self.assertEqual(unresolved, {absent})

    def test_unresolved_historical_context_is_hint_not_failure(self) -> None:
        value = MODULE.resolve_source_path(
            "domains/capital/planning/retirement.json",
            "src/legacy.py",
            set(),
            pointer="/retired/path",
        )
        self.assertEqual(value["standing"], "UNRESOLVED_IN_SOURCE_CUT")
        self.assertTrue(value["historicalContextHint"])

    def test_directory_reference_can_be_exact_without_being_a_file(self) -> None:
        value = MODULE.resolve_source_path(
            "apps/agent/README.md",
            "apps/agent",
            {"apps/agent/README.md"},
            directories={"apps", "apps/agent"},
            basename_index={"README.md": ["apps/agent/README.md"]},
        )
        self.assertEqual(value["standing"], "EXACT_UNIQUE")
        self.assertEqual(
            value["candidateKinds"],
            [{"path": "apps/agent", "kind": "directory"}],
        )

    def test_unique_basename_is_navigation_hint_not_relocation_claim(self) -> None:
        value = MODULE.resolve_source_path(
            ".agents/skills/example/SKILL.md",
            "../../../docs/EXAMPLE.md",
            {"legacy/archive/docs/EXAMPLE.md"},
            directories={
                ".agents",
                ".agents/skills",
                ".agents/skills/example",
                "meta",
                "legacy/archive",
                "legacy/archive/docs",
            },
            basename_index={"EXAMPLE.md": ["legacy/archive/docs/EXAMPLE.md"]},
            pointer="/reference",
        )
        self.assertEqual(value["standing"], "UNRESOLVED_IN_SOURCE_CUT")
        self.assertEqual(
            value["alternateLocationHints"],
            ["legacy/archive/docs/EXAMPLE.md"],
        )

    def test_path_candidate_filter_rejects_media_and_host_paths(self) -> None:
        self.assertFalse(
            MODULE.looks_like_source_path("application/vnd.apache.parquet", "mediaType")
        )
        self.assertFalse(
            MODULE.looks_like_source_path("usr/lib/libFreeCADApp.so", "libraryPath")
        )
        self.assertTrue(
            MODULE.looks_like_source_path("services/runtime/README.md", "sourcePath")
        )
        self.assertTrue(
            MODULE.looks_like_source_path("evidence/acceptance/result.json", "evidence")
        )

    def test_census_is_rebuildable_and_non_authoritative(self) -> None:
        left = self.census
        rebuilt_digest = MODULE.canonical_digest(
            {key: value for key, value in left.items() if key != "projectionDigest"}
        )
        self.assertEqual(left["projectionDigest"], rebuilt_digest)
        self.assertEqual(
            left["truthRole"],
            "rebuildable-source-reference-projection-not-semantic-live-or-domain-authority",
        )
        self.assertGreater(left["coverage"]["trackedFiles"], 0)
        self.assertGreater(left["coverage"]["topLevelKindFiles"], 0)
        self.assertGreater(left["coverage"]["uniqueTopLevelKinds"], 1)
        self.assertEqual(
            left["coverage"]["coverageClaim"],
            "BOUNDED_FORMAT_AND_SYNTAX_COVERAGE_NOT_SEMANTIC_COMPLETENESS",
        )

    def test_namespace_shape_does_not_mint_owner_binding(self) -> None:
        rows: list[dict[str, object]] = []
        counts = MODULE.Counter()
        MODULE._record_namespace(
            rows,
            counts,
            carrier="example.json",
            pointer="/ref",
            value="work:domain-local-id",
        )
        self.assertEqual(rows[0]["standing"], "OWNER_BINDING_UNKNOWN")

    def test_summary_does_not_promote_domain_relation_vocabulary(self) -> None:
        summary = MODULE.summarize_information_census(self.census)
        encoded = repr(summary)
        self.assertNotIn('"supports"', encoded)
        self.assertNotIn('"causes"', encoded)
        self.assertIn("summaryDigest", summary)


if __name__ == "__main__":
    unittest.main()
