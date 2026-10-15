from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry.providers import (  # noqa: E402
    AgentDojoRunAdapter,
    GarakReportAdapter,
    InspectEvalLogAdapter,
    PyritScenarioResultsAdapter,
    discovery_frontier,
    load_fixture,
)


class ProviderAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pyrit_path = ROOT / "fixtures/pyrit/scenario-results-attacks.synthetic.json"
        self.garak_path = ROOT / "fixtures/garak/report.synthetic.jsonl"
        self.agentdojo_path = ROOT / "fixtures/agentdojo/run.synthetic.json"
        self.inspect_path = ROOT / "fixtures/inspect/eval-log.synthetic.json"
        self.pyrit_ref = "fixtures/pyrit/scenario-results-attacks.synthetic.json"
        self.garak_ref = "fixtures/garak/report.synthetic.jsonl"
        self.agentdojo_ref = "fixtures/agentdojo/run.synthetic.json"
        self.inspect_ref = "fixtures/inspect/eval-log.synthetic.json"

    def test_pyrit_documented_attack_view_maps_without_claiming_world_state_truth(self) -> None:
        data = load_fixture(self.pyrit_path)
        rows = PyritScenarioResultsAdapter("fixture-doc-r1").parse_bytes(
            data,
            self.pyrit_ref,
            scenario_result_id="scenario-r1",
            target_id="synthetic:target-r1",
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].provider_outcome, "SUCCESS")
        self.assertIs(rows[0].provider_positive, True)
        self.assertIs(rows[1].provider_positive, False)
        self.assertIsNone(rows[2].provider_positive)
        self.assertEqual(rows[0].attack_family, "synthetic_indirect_injection")
        self.assertIn("provider judgment", " ".join(rows[0].notes))
        self.assertEqual(rows[0].artifact_ref.artifact_digest, "sha256:" + sha256(data).hexdigest())
        self.assertEqual(rows[2].score, None)

    def test_pyrit_adapter_fails_closed_when_documented_fields_are_missing(self) -> None:
        data = json.dumps([{"id": "broken", "technique": "x", "outcome": "SUCCESS"}]).encode()
        with self.assertRaisesRegex(ValueError, "missing documented fields"):
            PyritScenarioResultsAdapter("fixture-doc-r1").parse_bytes(
                data,
                "broken.json",
                scenario_result_id="scenario-r1",
                target_id="synthetic:target-r1",
            )

    def test_garak_eval_records_map_to_provider_specific_hit_rate(self) -> None:
        data = load_fixture(self.garak_path)
        rows = GarakReportAdapter("fixture-doc-r1").parse_bytes(
            data,
            self.garak_ref,
            provider_run_id="garak-r1",
        )
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0].score or 0.0, 0.25)
        self.assertIs(rows[0].provider_positive, True)
        self.assertEqual(rows[1].score, 0.0)
        self.assertIs(rows[1].provider_positive, False)
        self.assertEqual(rows[0].target_id, "synthetic:mock-agent-r1")
        self.assertEqual(rows[0].artifact_ref.artifact_digest, "sha256:" + sha256(data).hexdigest())
        self.assertIn("not normalized across probes", " ".join(rows[0].notes))

    def test_garak_absence_of_eval_records_is_not_treated_as_zero_findings(self) -> None:
        data = b'{"entry_type":"config","target_type":"synthetic","target_name":"x"}\n'
        with self.assertRaisesRegex(ValueError, "no eval records"):
            GarakReportAdapter("fixture-doc-r1").parse_bytes(data, "empty.jsonl", provider_run_id="g1")

    def test_garak_zero_evaluated_is_undetermined_not_safe(self) -> None:
        data = (
            b'{"entry_type":"config","target_type":"synthetic","target_name":"x"}\n'
            b'{"entry_type":"eval","probe":"p","detector":"d","passed":0,"total_evaluated":0}\n'
        )
        row = GarakReportAdapter("fixture-doc-r1").parse_bytes(data, "zero.jsonl", provider_run_id="g1")[0]
        self.assertEqual(row.provider_outcome, "provider_undetermined_zero_evaluated")
        self.assertIsNone(row.score)

    def test_discovery_frontier_counts_provider_positive_families_not_root_causes(self) -> None:
        rows = GarakReportAdapter("fixture-doc-r1").parse_bytes(
            load_fixture(self.garak_path),
            self.garak_ref,
            provider_run_id="g1",
        )
        frontier = discovery_frontier(rows, 2)
        self.assertEqual(frontier["positiveProviderFamilyCount"], 1)
        self.assertIn("not root-cause families", frontier["note"])

        pyrit_rows = PyritScenarioResultsAdapter("fixture-doc-r1").parse_bytes(
            load_fixture(self.pyrit_path),
            self.pyrit_ref,
            scenario_result_id="scenario-r1",
            target_id="synthetic:target-r1",
        )
        pyrit_frontier = discovery_frontier(pyrit_rows, 2)
        self.assertEqual(pyrit_frontier["positiveProviderFamilyCount"], 1)
        self.assertEqual(pyrit_frontier["positiveProviderFamilies"], ["synthetic_indirect_injection"])

    def test_agentdojo_adapter_preserves_utility_and_security_without_reinterpreting_them(self) -> None:
        data = load_fixture(self.agentdojo_path)
        row = AgentDojoRunAdapter("fixture-doc-r1").parse_bytes(data, self.agentdojo_ref)
        self.assertTrue(row.utility_flag)
        self.assertFalse(row.security_flag)
        self.assertEqual(row.attack_type, "synthetic_indirect_injection")
        self.assertIn("retained verbatim", row.interpretation)
        self.assertEqual(row.artifact_ref.artifact_digest, "sha256:" + sha256(data).hexdigest())

    def test_agentdojo_adapter_rejects_non_boolean_security_semantics(self) -> None:
        data = json.dumps(
            {
                "suite_name": "s",
                "pipeline_name": "p",
                "user_task_id": "u",
                "injection_task_id": "i",
                "attack_type": "a",
                "utility": True,
                "security": "unknown",
            }
        ).encode()
        with self.assertRaisesRegex(ValueError, "must remain booleans"):
            AgentDojoRunAdapter("fixture-doc-r1").parse_bytes(data, "bad.json")

    def test_provider_artifact_projects_onto_existing_security_evidence_ref_waist(self) -> None:
        data = load_fixture(self.pyrit_path)
        row = PyritScenarioResultsAdapter("fixture-doc-r1").parse_bytes(
            data,
            self.pyrit_ref,
            scenario_result_id="scenario-r1",
            target_id="synthetic:target-r1",
        )[0]
        projection = row.artifact_ref.to_security_evidence_ref_projection()
        self.assertEqual(
            projection,
            {
                "provider": "pyrit",
                "format": "scenario-results.attacks.json",
                "path": self.pyrit_ref,
                "sha256": "sha256:" + sha256(data).hexdigest(),
                "byte_length": len(data),
            },
        )

    def test_inspect_adapter_uses_eval_log_as_common_evaluation_evidence_surface(self) -> None:
        data = load_fixture(self.inspect_path)
        projection = InspectEvalLogAdapter("fixture-doc-r1").parse_bytes(data, self.inspect_ref)
        self.assertEqual(projection.eval_id, "fixture-eval-001")
        self.assertEqual(projection.run_id, "fixture-run-001")
        self.assertEqual(projection.task, "agent_threat_bench_memory_poison")
        self.assertEqual(projection.model, "mock/synthetic-agent")
        self.assertEqual(projection.sample_count, 2)
        self.assertEqual(projection.scorer_names, ("security", "utility"))
        self.assertIn(("inspect_ai", "fixture-version"), projection.package_versions)
        self.assertIn("task-version-specific interpretation", projection.interpretation)
        self.assertEqual(
            projection.artifact_ref.to_security_evidence_ref_projection()["path"],
            self.inspect_ref,
        )

    def test_inspect_adapter_rejects_incomplete_eval_identity(self) -> None:
        data = json.dumps(
            {
                "version": 2,
                "status": "success",
                "eval": {"eval_id": "x"},
                "samples": [],
            }
        ).encode()
        with self.assertRaisesRegex(ValueError, "EvalSpec missing documented fields"):
            InspectEvalLogAdapter("fixture-doc-r1").parse_bytes(data, "fixtures/inspect/bad.json")


if __name__ == "__main__":
    unittest.main()
