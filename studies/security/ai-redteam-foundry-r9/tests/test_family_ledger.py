from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (
    ROOT,
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8",
):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r8 import SearchCandidateRef, SearchResultRef  # noqa: E402
from foundry_r9 import FamilyAssignment, FamilyHypothesis, build_family_ledger, discovery_frontier  # noqa: E402

D = lambda c: "sha256:" + c * 64
RUN = D("a")


def result(sequence: int, family: str, *, positive: bool | None = True, observed: bool = False) -> SearchResultRef:
    digit = format(sequence % 16, "x")
    artifact = ProviderArtifactRef("provider", "v1", "fixture.json", D(digit), 10 + sequence, f"case-{sequence}.json")
    candidate = SearchCandidateRef(
        search_run_digest=RUN,
        sequence=sequence,
        provider="provider",
        provider_version="v1",
        provider_run_id="run:1",
        provider_case_id=f"case:{sequence}",
        attack_family=family,
        target_id="target:1",
        provider_projection_digest=D(format((sequence + 4) % 16, "x")),
        candidate_identity_digest=D(format((sequence + 8) % 16, "x")),
        artifact_ref=artifact,
    )
    return SearchResultRef(
        candidate=candidate,
        judge_id="judge:provider",
        provider_outcome="signal" if positive is not None else "undetermined",
        provider_positive=positive,
        score=0.8 if positive is True else 0.1 if positive is False else None,
        observation_digest=D("f") if observed else None,
        observed_effect_id="effect:1" if observed else None,
        observed_effect_request_digest=D("e") if observed else None,
    )


def hypothesis(hid: str, mechanism: str) -> FamilyHypothesis:
    suffix = "1" if hid.endswith("1") else "2"
    return FamilyHypothesis(hid, mechanism, "synthetic_agent", D(suffix), D("c" if suffix == "1" else "d"))


def assign(item: SearchResultRef, hid: str, *, method: str = "manual_analysis") -> FamilyAssignment:
    return FamilyAssignment(item.digest, hid, method, "analysis:r9-fixture", D("b"))


class FamilyLedgerTests(unittest.TestCase):
    def test_different_provider_labels_can_share_one_root_cause_family(self) -> None:
        a = result(1, "surface-a")
        b = result(2, "surface-b", observed=True)
        h = hypothesis("hypothesis:1", "instruction_data_provenance_confusion")
        ledger = build_family_ledger((a, b), (h,), (assign(a, h.hypothesis_id), assign(b, h.hypothesis_id)))
        self.assertEqual(len(ledger.entries), 1)
        self.assertEqual(ledger.entries[0].provider_attack_families, ("surface-a", "surface-b"))
        self.assertEqual(ledger.entries[0].observer_bound_member_count, 1)

    def test_identical_provider_label_can_map_to_different_root_causes(self) -> None:
        a = result(1, "same-surface")
        b = result(2, "same-surface")
        h1 = hypothesis("hypothesis:1", "instruction_data_provenance_confusion")
        h2 = hypothesis("hypothesis:2", "authority_boundary_confusion")
        ledger = build_family_ledger((a, b), (h1, h2), (assign(a, h1.hypothesis_id), assign(b, h2.hypothesis_id)))
        self.assertEqual({entry.family_id for entry in ledger.entries}, {h1.family_id, h2.family_id})

    def test_family_identity_is_stable_when_members_are_added(self) -> None:
        a = result(1, "a")
        b = result(2, "b")
        h = hypothesis("hypothesis:1", "mechanism")
        one = build_family_ledger((a,), (h,), (assign(a, h.hypothesis_id),)).entries[0]
        two = build_family_ledger((a, b), (h,), (assign(a, h.hypothesis_id), assign(b, h.hypothesis_id))).entries[0]
        self.assertEqual(one.family_id, two.family_id)
        self.assertNotEqual(one.digest, two.digest)

    def test_duplicate_assignment_fails_closed(self) -> None:
        a = result(1, "a")
        h1 = hypothesis("hypothesis:1", "m1")
        h2 = hypothesis("hypothesis:2", "m2")
        with self.assertRaisesRegex(ValueError, "multiple"):
            build_family_ledger((a,), (h1, h2), (assign(a, h1.hypothesis_id), assign(a, h2.hypothesis_id)))

    def test_unknown_result_assignment_fails_closed(self) -> None:
        a = result(1, "a")
        h = hypothesis("hypothesis:1", "m1")
        bad = replace(assign(a, h.hypothesis_id), result_digest=D("9"))
        with self.assertRaisesRegex(ValueError, "unknown R8 result"):
            build_family_ledger((a,), (h,), (bad,))

    def test_unassigned_result_remains_explicit(self) -> None:
        a = result(1, "a")
        b = result(2, "b")
        h = hypothesis("hypothesis:1", "m1")
        ledger = build_family_ledger((a, b), (h,), (assign(a, h.hypothesis_id),))
        self.assertEqual(ledger.unassigned_result_digests, (b.digest,))

    def test_provider_positive_does_not_create_family_without_assignment(self) -> None:
        a = result(1, "provider-positive", positive=True)
        ledger = build_family_ledger((a,), (), ())
        self.assertEqual(ledger.entries, ())
        self.assertEqual(ledger.unassigned_result_digests, (a.digest,))

    def test_discovery_frontier_is_monotone_by_root_cause_family(self) -> None:
        a = result(1, "a")
        b = result(2, "b")
        c = result(3, "c")
        h1 = hypothesis("hypothesis:1", "m1")
        h2 = hypothesis("hypothesis:2", "m2")
        assignments = (assign(a, h1.hypothesis_id), assign(b, h1.hypothesis_id), assign(c, h2.hypothesis_id))
        frontier = discovery_frontier(RUN, (c, a, b), (h1, h2), assignments)
        self.assertEqual(frontier.points[0].newly_discovered_family_ids, (h1.family_id,))
        self.assertEqual(frontier.points[1].newly_discovered_family_ids, ())
        self.assertEqual(frontier.points[2].newly_discovered_family_ids, (h2.family_id,))
        self.assertEqual(frontier.points[2].cumulative_family_ids, tuple(sorted((h1.family_id, h2.family_id))))

    def test_external_clusterer_assignment_keeps_method_ref(self) -> None:
        a = result(1, "a")
        h = hypothesis("hypothesis:1", "m1")
        assignment = FamilyAssignment(a.digest, h.hypothesis_id, "external_clusterer", "clusterer:hdbscan@fixture", D("7"))
        ledger = build_family_ledger((a,), (h,), (assignment,))
        self.assertEqual(ledger.assignment_digests, (assignment.digest,))


if __name__ == "__main__":
    unittest.main()
