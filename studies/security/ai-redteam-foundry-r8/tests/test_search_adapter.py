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
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r6",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r7",
):
    sys.path.insert(0, str(path))

from foundry.providers import PyritScenarioResultsAdapter  # noqa: E402
from foundry_r4 import ExperimentEnvironmentSpec, IsolationVector, ResourceBudget, SandboxProviderBinding, canonical_digest  # noqa: E402
from foundry_r5 import InMemorySyntheticWorld, SyntheticIdentity, SyntheticService, SyntheticWorldSpec  # noqa: E402
from foundry_r6 import EffectAttempt, ReferenceEffectProxy  # noqa: E402
from foundry_r7 import SyntheticWorldObserver  # noqa: E402
from foundry_r8 import SearchBudget, SearchControl, bind_search_run, normalize_provider_batch, normalize_provider_projection  # noqa: E402

D = lambda c: "sha256:" + c * 64


def environment(world_digest: str, *, threat_class: str = "synthetic_agent") -> ExperimentEnvironmentSpec:
    observer_digest = canonical_digest(SyntheticWorldObserver.binding.to_dict())
    return ExperimentEnvironmentSpec(
        environment_id="env:r8-test",
        threat_class=threat_class,
        base_image_digest=D("a"),
        synthetic_world_digest=world_digest,
        tool_surface_digest=D("b"),
        observer_spec_digest=observer_digest,
        isolation=IsolationVector(
            process="separate_process_tree",
            kernel="shared",
            filesystem="synthetic",
            network="none",
            credentials="synthetic_only",
            devices="none",
            external_effects="synthetic_only",
            lifecycle="resettable",
            observer="independent",
        ),
        budget=ResourceBudget(60, 30, 512, 128, 32, 0),
        provider=SandboxProviderBinding("synthetic-r5", "r5", "synthetic_world", D("c")),
    )


def run_spec(world_digest: str, *, max_candidates: int = 8):
    return bind_search_run(
        search_id="search:r8-test",
        provider="pyrit",
        provider_version="synthetic-fixture-v1",
        provider_engine="scenario-results-attacks",
        provider_run_id="pyrit-run:r8-test",
        target_id="target:r8-test",
        environment=environment(world_digest),
        observer_binding=SyntheticWorldObserver.binding,
        seed_artifact_digest=D("d"),
        provider_config_digest=D("e"),
        budget=SearchBudget(max_candidates, 4, max_candidates * 4, 60000),
        control=SearchControl(7, "fixed_sequence", "none"),
    )


def pyrit_rows():
    data = (REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1" / "fixtures" / "pyrit" / "scenario-results-attacks.synthetic.json").read_bytes()
    return PyritScenarioResultsAdapter("synthetic-fixture-v1").parse_bytes(
        data,
        "fixtures/pyrit/scenario-results-attacks.synthetic.json",
        scenario_result_id="pyrit-run:r8-test",
        target_id="target:r8-test",
    )


class SearchAdapterTests(unittest.TestCase):
    def test_run_binds_environment_observer_seed_budget_and_adaptivity(self) -> None:
        run = run_spec(D("f"))
        self.assertEqual(run.threat_class, "synthetic_agent")
        self.assertEqual(run.budget.max_candidates, 8)
        self.assertEqual(run.control.random_seed, 7)
        self.assertEqual(run.control.adaptivity, "fixed_sequence")
        self.assertEqual(run.observer_binding_digest, canonical_digest(SyntheticWorldObserver.binding.to_dict()))

    def test_hostile_code_rejects_process_local_observer(self) -> None:
        env = environment(D("f"), threat_class="hostile_code")
        env = replace(
            env,
            isolation=IsolationVector(
                process="vm",
                kernel="separate_guest_kernel",
                filesystem="disposable_overlay",
                network="none",
                credentials="none",
                devices="none",
                external_effects="none",
                lifecycle="disposable",
                observer="independent",
            ),
        )
        with self.assertRaisesRegex(ValueError, "observer binding"):
            bind_search_run(
                search_id="search:hostile",
                provider="pyrit",
                provider_version="v",
                provider_engine="scenario",
                provider_run_id="run",
                target_id="target",
                environment=env,
                observer_binding=SyntheticWorldObserver.binding,
                seed_artifact_digest=D("d"),
                provider_config_digest=D("e"),
                budget=SearchBudget(1, 1, 1, 1000),
                control=SearchControl(0, "fixed_sequence", "none"),
            )

    def test_provider_projection_normalizes_deterministically(self) -> None:
        rows = pyrit_rows()
        run = run_spec(D("f"), max_candidates=len(rows))
        first = normalize_provider_batch(run, rows)
        second = normalize_provider_batch(run, rows)
        self.assertEqual([item.digest for item in first], [item.digest for item in second])
        self.assertEqual([item.candidate.sequence for item in first], list(range(1, len(rows) + 1)))
        self.assertNotIn("securityStanding", first[0].to_dict())

    def test_projection_version_drift_fails_closed(self) -> None:
        row = replace(pyrit_rows()[0], provider_version="other")
        with self.assertRaisesRegex(ValueError, "version drifted"):
            normalize_provider_projection(run_spec(D("f")), row, sequence=1)

    def test_projection_run_identity_drift_fails_closed(self) -> None:
        row = replace(pyrit_rows()[0], provider_run_id="other-run")
        with self.assertRaisesRegex(ValueError, "different provider run"):
            normalize_provider_projection(run_spec(D("f")), row, sequence=1)

    def test_projection_target_drift_fails_closed(self) -> None:
        row = replace(pyrit_rows()[0], target_id="other-target")
        with self.assertRaisesRegex(ValueError, "different target"):
            normalize_provider_projection(run_spec(D("f")), row, sequence=1)

    def test_candidate_budget_is_enforced(self) -> None:
        rows = pyrit_rows()
        with self.assertRaisesRegex(ValueError, "candidate budget"):
            normalize_provider_batch(run_spec(D("f"), max_candidates=1), rows)

    def test_adaptivity_feedback_owner_is_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "provider-owned"):
            SearchControl(1, "provider_adaptive", "observer:r7")
        with self.assertRaisesRegex(ValueError, "observer-owned"):
            SearchControl(1, "observer_adaptive", "provider:score")
        self.assertEqual(SearchControl(1, "observer_adaptive", "observer:r7").feedback_source, "observer:r7")

    def test_observation_binding_is_world_native_not_provider_outcome(self) -> None:
        world = InMemorySyntheticWorld(
            SyntheticWorldSpec(
                world_id="world:r8-observation",
                identities=(SyntheticIdentity("agent:test"),),
                services=(SyntheticService("mail:test", "mail"),),
                resources=(),
            )
        )
        env = environment(world.spec.digest)
        run = bind_search_run(
            search_id="search:r8-observed",
            provider="pyrit",
            provider_version="synthetic-fixture-v1",
            provider_engine="scenario-results-attacks",
            provider_run_id="pyrit-run:r8-test",
            target_id="target:r8-test",
            environment=env,
            observer_binding=SyntheticWorldObserver.binding,
            seed_artifact_digest=D("d"),
            provider_config_digest=D("e"),
            budget=SearchBudget(8, 4, 32, 60000),
            control=SearchControl(7, "observer_adaptive", "observer:r7"),
        )
        observer = SyntheticWorldObserver()
        anchor = observer.start(world, environment_digest=env.digest)
        attempt = EffectAttempt(
            effect_id="effect:r8-observed",
            actor_id="agent:test",
            environment_digest=env.digest,
            world_spec_digest=world.spec.digest,
            scope="synthetic_world",
            service_id="mail:test",
            operation="send",
            target="sink@example.test",
            content="synthetic",
        )
        ReferenceEffectProxy(world).handle(attempt)
        observation = observer.finish(anchor, world, effect_id=attempt.effect_id, effect_request_digest=attempt.digest)
        result = normalize_provider_projection(run, pyrit_rows()[0], sequence=1, observation=observation)
        self.assertEqual(result.observation_digest, observation.digest)
        self.assertEqual(result.observed_effect_request_digest, attempt.digest)

    def test_observation_from_other_environment_fails_closed(self) -> None:
        world = InMemorySyntheticWorld(
            SyntheticWorldSpec(
                world_id="world:r8-other-env",
                identities=(SyntheticIdentity("agent:test"),),
                services=(SyntheticService("mail:test", "mail"),),
                resources=(),
            )
        )
        run = run_spec(world.spec.digest)
        observer = SyntheticWorldObserver()
        anchor = observer.start(world, environment_digest=D("9"))
        attempt = EffectAttempt(
            effect_id="effect:r8-other-env",
            actor_id="agent:test",
            environment_digest=D("9"),
            world_spec_digest=world.spec.digest,
            scope="synthetic_world",
            service_id="mail:test",
            operation="send",
            target="sink@example.test",
            content="synthetic",
        )
        ReferenceEffectProxy(world).handle(attempt)
        observation = observer.finish(anchor, world, effect_id=attempt.effect_id, effect_request_digest=attempt.digest)
        with self.assertRaisesRegex(ValueError, "different R4 environment"):
            normalize_provider_projection(run, pyrit_rows()[0], sequence=1, observation=observation)

    def test_provider_artifact_ref_projects_to_existing_security_evidence_waist(self) -> None:
        row = pyrit_rows()[0]
        result = normalize_provider_projection(run_spec(D("f")), row, sequence=1)
        projection = result.candidate.artifact_ref.to_security_evidence_ref_projection()
        self.assertEqual(projection["sha256"], row.artifact_ref.artifact_digest)
        self.assertEqual(projection["provider"], "pyrit")


if __name__ == "__main__":
    unittest.main()
