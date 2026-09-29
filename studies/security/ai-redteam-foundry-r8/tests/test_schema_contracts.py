from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (
    ROOT,
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r4",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r7",
):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef, ProviderFindingProjection  # noqa: E402
from foundry_r4 import ExperimentEnvironmentSpec, IsolationVector, ResourceBudget, SandboxProviderBinding, canonical_digest  # noqa: E402
from foundry_r7 import SyntheticWorldObserver  # noqa: E402
from foundry_r8 import SearchBudget, SearchControl, bind_search_run, normalize_provider_projection  # noqa: E402

D = lambda c: "sha256:" + c * 64


class SchemaContractTests(unittest.TestCase):
    def schema(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def assert_exact_top_level(self, schema: dict[str, object], payload: dict[str, object]) -> None:
        self.assertEqual(set(schema["properties"]), set(payload))
        self.assertTrue(set(schema["required"]).issubset(payload))

    def run_and_result(self):
        observer_digest = canonical_digest(SyntheticWorldObserver.binding.to_dict())
        env = ExperimentEnvironmentSpec(
            environment_id="env:r8-schema",
            threat_class="synthetic_agent",
            base_image_digest=D("a"),
            synthetic_world_digest=D("b"),
            tool_surface_digest=D("c"),
            observer_spec_digest=observer_digest,
            isolation=IsolationVector("separate_process_tree", "shared", "synthetic", "none", "synthetic_only", "none", "synthetic_only", "resettable", "independent"),
            budget=ResourceBudget(60, 30, 512, 128, 32, 0),
            provider=SandboxProviderBinding("synthetic-r5", "r5", "synthetic_world", D("d")),
        )
        run = bind_search_run(
            search_id="search:r8-schema",
            provider="synthetic-provider",
            provider_version="v1",
            provider_engine="fixture",
            provider_run_id="run:r8-schema",
            target_id="target:r8-schema",
            environment=env,
            observer_binding=SyntheticWorldObserver.binding,
            seed_artifact_digest=D("e"),
            provider_config_digest=D("f"),
            budget=SearchBudget(2, 1, 2, 1000),
            control=SearchControl(1, "fixed_sequence", "none"),
        )
        artifact = ProviderArtifactRef("synthetic-provider", "v1", "fixture.json", D("1"), 12, "fixture.json")
        projection = ProviderFindingProjection(
            provider="synthetic-provider",
            provider_version="v1",
            provider_run_id="run:r8-schema",
            provider_case_id="case:1",
            attack_family="fixture-family",
            target_id="target:r8-schema",
            judge_id="judge:fixture",
            provider_outcome="provider_signal",
            provider_positive=None,
            score=None,
            artifact_ref=artifact,
            projection_digest=D("2"),
        )
        return run, normalize_provider_projection(run, projection, sequence=1)

    def test_run_schema_matches_serialization(self) -> None:
        run, _ = self.run_and_result()
        self.assert_exact_top_level(self.schema("attack-search-run.schema.json"), run.to_dict())

    def test_result_schema_matches_serialization(self) -> None:
        _, result = self.run_and_result()
        self.assert_exact_top_level(self.schema("search-result-ref.schema.json"), result.to_dict())


if __name__ == "__main__":
    unittest.main()
