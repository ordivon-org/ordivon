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
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r4",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r9",
):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r4 import ExperimentEnvironmentSpec, IsolationVector, ResourceBudget, SandboxProviderBinding, canonical_digest  # noqa: E402
from foundry_r8 import SearchBudget, SearchCandidateRef, SearchControl, SearchResultRef, bind_search_run  # noqa: E402
from foundry_r9 import FamilyAssignment, FamilyHypothesis, build_family_ledger, discovery_frontier  # noqa: E402
from foundry_r10 import PatchBinding, UtilityEvaluationRef, bind_search_phase, build_regression_receipt  # noqa: E402

D = lambda c: "sha256:" + c * 64
PATCH = PatchBinding("patch:1", "owner:test", D("1"), "target:before", D("2"), "target:after", D("3"))


def environment() -> ExperimentEnvironmentSpec:
    return ExperimentEnvironmentSpec(
        environment_id="env:r10",
        threat_class="synthetic_agent",
        base_image_digest=D("4"),
        synthetic_world_digest=D("5"),
        tool_surface_digest=D("6"),
        observer_spec_digest=D("7"),
        isolation=IsolationVector("separate_process_tree", "shared", "synthetic", "none", "synthetic_only", "none", "synthetic_only", "resettable", "independent"),
        budget=ResourceBudget(60, 30, 512, 128, 32, 0),
        provider=SandboxProviderBinding("fixture", "r10", "synthetic", D("8")),
    )


def run(run_id: str, max_candidates: int, *, fixed: bool = False):
    # R10 consumes already-admitted R8 runs; for this unit fixture construct the exact R8 value directly
    # because the R7 observer digest belongs to a separate owner and is not the object under test here.
    return __import__("foundry_r8").AttackSearchRunSpec(
        search_id=f"search:{run_id}",
        provider="fixture-provider",
        provider_version="v1",
        provider_engine="fixture-engine",
        provider_run_id=run_id,
        target_id=PATCH.target_after_id,
        threat_class="synthetic_agent",
        environment_digest=D("9"),
        world_spec_digest=D("a"),
        observer_binding_digest=D("b"),
        seed_artifact_digest=D("c"),
        provider_config_digest=D("d"),
        budget=SearchBudget(max_candidates, max(1, max_candidates), max_candidates * 2, 60000),
        control=SearchControl(1, "fixed_sequence" if fixed else "provider_adaptive", "none" if fixed else "provider:fixture"),
    )


def result(search_run, sequence: int, *, positive: bool | None = False) -> SearchResultRef:
    digit = format((sequence + 1) % 16, "x")
    artifact = ProviderArtifactRef("fixture-provider", "v1", "fixture.json", D(digit), 10 + sequence, f"fixture-{sequence}.json")
    candidate = SearchCandidateRef(search_run.digest, sequence, "fixture-provider", "v1", search_run.provider_run_id, f"case:{sequence}", "surface", PATCH.target_after_id, D(format((sequence + 5) % 16, "x")), D(format((sequence + 9) % 16, "x")), artifact)
    return SearchResultRef(candidate, "judge", "signal", positive, 0.9 if positive else 0.1 if positive is False else None, None, None, None)


def family_for(item: SearchResultRef, hid: str = "hypothesis:source"):
    h = FamilyHypothesis(hid, "root-cause", "synthetic_agent", D("e"), D("f"))
    a = FamilyAssignment(item.digest, h.hypothesis_id, "manual_analysis", "analysis:r10", D("1"))
    ledger = build_family_ledger((item,), (h,), (a,))
    frontier = discovery_frontier(item.candidate.search_run_digest, (item,), (h,), (a,))
    return h, ledger, frontier


def empty_evidence(search_run, rows):
    ledger = build_family_ledger(tuple(rows), (), ())
    frontier = discovery_frontier(search_run.digest, tuple(rows), (), ())
    return ledger, frontier


def phase(name: str, search_run, rows, *, ledger=None, frontier=None, expected=None, coverage=True, review=True):
    rows = tuple(rows)
    if ledger is None or frontier is None:
        ledger, frontier = empty_evidence(search_run, rows)
    return bind_search_phase(
        phase=name,
        run=search_run,
        results=rows,
        family_ledger=ledger,
        frontier=frontier,
        patch=PATCH,
        provider_completion_digest=D("2"),
        review_evidence_digest=D("3"),
        expected_candidate_count=expected if expected is not None else len(rows),
        coverage_complete=coverage,
        review_complete=review,
    )


def source_family():
    search_run = run("source", 1, fixed=True)
    item = result(search_run, 1, positive=True)
    _, ledger, _ = family_for(item)
    return ledger.entries[0], ledger


def utility(*, complete=True, failed=0, target_id=None, target_digest=None):
    artifact = ProviderArtifactRef("agentdojo", "fixture-v1", "utility.json", D("4"), 100, "utility.json")
    return UtilityEvaluationRef("utility:r10", target_id or PATCH.target_after_id, target_digest or PATCH.target_after_digest, 4, failed, complete, artifact)


def passing_phases():
    replay_run = run("replay", 1, fixed=True)
    mutation_run = run("mutation", 2)
    reattack_run = run("reattack", 2)
    return (
        phase("original_replay", replay_run, (result(replay_run, 1),), expected=1),
        phase("family_mutation", mutation_run, (result(mutation_run, 1), result(mutation_run, 2)), expected=2),
        phase("defense_aware_reattack", reattack_run, (result(reattack_run, 1), result(reattack_run, 2)), expected=2),
    )


class RegressionLoopTests(unittest.TestCase):
    def receipt(self, phases=None, util=None):
        entry, ledger = source_family()
        return build_regression_receipt(source_family_entry=entry, source_family_ledger=ledger, patch=PATCH, phases=phases or passing_phases(), utility=util or utility())

    def test_complete_family_free_search_and_utility_pass(self) -> None:
        receipt = self.receipt()
        self.assertEqual(receipt.standing, "PASS")
        self.assertEqual(receipt.residual_family_ids, ())

    def test_incomplete_attack_coverage_never_passes(self) -> None:
        phases = list(passing_phases())
        runx = run("mutation-incomplete", 2)
        phases[1] = phase("family_mutation", runx, (result(runx, 1),), expected=2, coverage=False)
        self.assertEqual(self.receipt(tuple(phases)).standing, "INCOMPLETE")

    def test_incomplete_review_never_passes(self) -> None:
        phases = list(passing_phases())
        runx = run("mutation-review", 1)
        phases[1] = phase("family_mutation", runx, (result(runx, 1),), expected=1, review=False)
        self.assertEqual(self.receipt(tuple(phases)).standing, "INCOMPLETE")

    def test_unassigned_provider_positive_keeps_phase_incomplete(self) -> None:
        phases = list(passing_phases())
        runx = run("mutation-positive", 1)
        positive = result(runx, 1, positive=True)
        phases[1] = phase("family_mutation", runx, (positive,), expected=1)
        self.assertEqual(phases[1].unassigned_provider_positive_count, 1)
        self.assertEqual(self.receipt(tuple(phases)).standing, "INCOMPLETE")

    def test_original_family_replay_hit_fails(self) -> None:
        phases = list(passing_phases())
        replay = run("replay-hit", 1, fixed=True)
        item = result(replay, 1, positive=True)
        _, ledger, frontier = family_for(item)
        phases[0] = phase("original_replay", replay, (item,), ledger=ledger, frontier=frontier, expected=1)
        receipt = self.receipt(tuple(phases))
        self.assertEqual(receipt.standing, "FAIL")
        self.assertTrue(receipt.residual_family_ids)

    def test_new_different_family_after_patch_also_fails(self) -> None:
        phases = list(passing_phases())
        attack = run("reattack-new-family", 1)
        item = result(attack, 1, positive=True)
        h = FamilyHypothesis("hypothesis:new", "different-root-cause", "synthetic_agent", D("6"), D("7"))
        a = FamilyAssignment(item.digest, h.hypothesis_id, "manual_analysis", "analysis:new", D("8"))
        ledger = build_family_ledger((item,), (h,), (a,))
        frontier = discovery_frontier(attack.digest, (item,), (h,), (a,))
        phases[2] = phase("defense_aware_reattack", attack, (item,), ledger=ledger, frontier=frontier, expected=1)
        receipt = self.receipt(tuple(phases))
        self.assertEqual(receipt.standing, "FAIL")
        self.assertIn(h.family_id, receipt.residual_family_ids)

    def test_utility_failure_fails(self) -> None:
        self.assertEqual(self.receipt(util=utility(failed=1)).standing, "FAIL")

    def test_incomplete_utility_is_incomplete(self) -> None:
        self.assertEqual(self.receipt(util=utility(complete=False)).standing, "INCOMPLETE")

    def test_target_after_identity_mismatch_rejected(self) -> None:
        bad_utility = utility(target_digest=D("9"))
        with self.assertRaisesRegex(ValueError, "utility evaluation target"):
            self.receipt(util=bad_utility)

    def test_search_run_target_id_mismatch_rejected(self) -> None:
        search_run = replace(run("bad-target", 1), target_id="target:other")
        rows = (result(search_run, 1),)
        ledger, frontier = empty_evidence(search_run, rows)
        with self.assertRaisesRegex(ValueError, "patched target"):
            bind_search_phase(phase="family_mutation", run=search_run, results=rows, family_ledger=ledger, frontier=frontier, patch=PATCH, provider_completion_digest=D("2"), review_evidence_digest=D("3"), expected_candidate_count=1, coverage_complete=True, review_complete=True)

    def test_original_replay_requires_exactly_one_candidate(self) -> None:
        search_run = run("bad-replay", 2, fixed=True)
        rows = (result(search_run, 1), result(search_run, 2))
        ledger, frontier = empty_evidence(search_run, rows)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            bind_search_phase(phase="original_replay", run=search_run, results=rows, family_ledger=ledger, frontier=frontier, patch=PATCH, provider_completion_digest=D("2"), review_evidence_digest=D("3"), expected_candidate_count=2, coverage_complete=True, review_complete=True)

    def test_original_replay_requires_fixed_sequence(self) -> None:
        search_run = run("adaptive-replay", 1, fixed=False)
        rows = (result(search_run, 1),)
        ledger, frontier = empty_evidence(search_run, rows)
        with self.assertRaisesRegex(ValueError, "fixed-sequence"):
            bind_search_phase(phase="original_replay", run=search_run, results=rows, family_ledger=ledger, frontier=frontier, patch=PATCH, provider_completion_digest=D("2"), review_evidence_digest=D("3"), expected_candidate_count=1, coverage_complete=True, review_complete=True)

    def test_receipt_is_deterministic(self) -> None:
        self.assertEqual(self.receipt().digest, self.receipt().digest)
        self.assertEqual(self.receipt().evidence_digest, self.receipt().evidence_digest)

    def test_provider_utility_artifact_identity_is_retained(self) -> None:
        receipt = self.receipt()
        self.assertEqual(receipt.utility.artifact_ref.provider, "agentdojo")
        self.assertEqual(receipt.utility.to_dict()["artifactRef"]["artifactDigest"], D("4"))


if __name__ == "__main__":
    unittest.main()
