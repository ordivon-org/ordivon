#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("living_view.py")
SPEC = importlib.util.spec_from_file_location("living_view", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LivingViewTests(unittest.TestCase):
    def test_source_view_is_digest_stable_and_owner_graph_is_projection_only(
        self,
    ) -> None:
        left = MODULE.build_source_view("HEAD")
        right = MODULE.build_source_view("HEAD")
        self.assertEqual(left["viewDigest"], right["viewDigest"])
        self.assertEqual(
            left["truthRole"],
            "rebuildable-source-projection-not-live-or-domain-authority",
        )
        graph = left["repositoryOwnerGraph"]
        self.assertEqual(
            graph["truthRole"],
            "repository-mechanics-only-not-domain-authority",
        )
        self.assertEqual(
            graph["independenceClaim"], "NOT_ESTABLISHED_BY_THIS_PROJECTION"
        )
        self.assertTrue(graph["owners"])
        information = left["informationCoverage"]
        self.assertEqual(
            information["truthRole"],
            "rebuildable-source-reference-projection-not-semantic-live-or-domain-authority",
        )
        self.assertEqual(
            information["coverage"]["coverageClaim"],
            "BOUNDED_FORMAT_AND_SYNTAX_COVERAGE_NOT_SEMANTIC_COMPLETENESS",
        )
        self.assertGreater(information["coverage"]["uniqueTopLevelKinds"], 1)

    def test_unowned_change_is_not_silently_attributed(self) -> None:
        by_owner, cross_cutting, unowned = MODULE._path_owner_classification(
            ["README.md", "services/runtime/README.md"]
        )
        self.assertEqual(cross_cutting, [])
        self.assertEqual(by_owner["runtime"], ["services/runtime/README.md"])
        self.assertEqual(unowned, ["README.md"])

    def test_cross_cutting_change_is_distinct_from_owner_local_change(self) -> None:
        by_owner, cross_cutting, unowned = MODULE._path_owner_classification(
            ["tools/repo/owners.toml"]
        )
        self.assertEqual(by_owner, {})
        self.assertEqual(cross_cutting, ["tools/repo/owners.toml"])
        self.assertEqual(unowned, [])

    def test_required_missing_observation_remains_unknown(self) -> None:
        source = MODULE.build_source_view("HEAD")
        view = MODULE.build_qualified_view(
            source,
            required_observation_owners=["gateway", "runtime"],
        )
        self.assertEqual(view["unknownRequiredOwners"], ["gateway", "runtime"])

    def test_observations_do_not_overwrite_source_truth(self) -> None:
        source = MODULE.build_source_view("HEAD")
        observation = {
            "schemaVersion": 1,
            "kind": "ordivon.living-owner-observation",
            "subjectRef": "owner:gateway",
            "ownerRef": "gateway",
            "observedAt": "2026-10-01T20:00:00+08:00",
            "operation": "system.describe",
            "standing": "AVAILABLE",
            "evidenceRefs": ["runtime:artifact:example"],
            "attributes": {"version": "0.8.0"},
            "sourceRevision": "different-revision",
        }
        view = MODULE.build_qualified_view(
            source,
            observations=[observation],
            required_observation_owners=["gateway"],
        )
        self.assertEqual(view["unknownRequiredOwners"], [])
        row = view["ownerObservations"][0]
        self.assertEqual(
            row["sourceBindingRelation"],
            "DIFFERENT_SOURCE_REVISION_NO_SEMANTIC_INFERENCE",
        )
        self.assertEqual(source["sourceRevision"], view["sourceView"]["sourceRevision"])

    def test_ci_persists_living_view_before_repository_mechanics(self) -> None:
        workflow = (MODULE.ROOT / ".github/workflows/ci.yml").read_text(
            encoding="utf-8"
        )
        build = workflow.index("- name: Build Living Recursive LEGO View")
        retain = workflow.index("- name: Retain Living Recursive LEGO View")
        mechanics = workflow.index("- name: Repository mechanics")
        self.assertLess(build, retain)
        self.assertLess(retain, mechanics)

    def test_load_observation_accepts_single_or_array(self) -> None:
        row = {
            "schemaVersion": 1,
            "kind": "ordivon.living-owner-observation",
            "subjectRef": "owner:host",
            "ownerRef": "host",
            "observedAt": "2026-10-01T20:00:00+08:00",
            "operation": "host.status",
            "standing": "HEALTHY",
            "evidenceRefs": [],
            "attributes": {"schema": 10},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            one = root / "one.json"
            many = root / "many.json"
            one.write_text(json.dumps(row), encoding="utf-8")
            many.write_text(json.dumps([row]), encoding="utf-8")
            self.assertEqual(len(MODULE.load_observations([one])), 1)
            self.assertEqual(len(MODULE.load_observations([many])), 1)


if __name__ == "__main__":
    unittest.main()
