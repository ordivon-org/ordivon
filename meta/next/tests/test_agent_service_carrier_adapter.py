from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_service import CarrierProviderAdapter as ExportedCarrierProviderAdapter
from agent_service.slice1 import AgentRevision, AgentServiceSlice1, CarrierProviderAdapter, HostAdapter, ProviderObservation
from agent_service.carriers.agent_automation import (
    AgentAutomationCarrierAdapter,
    CarrierCommandError,
    CarrierProfileError,
    CarrierRetireUnsupported,
)


class FakeRunner:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = list(responses)
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> dict:
        self.calls.append(list(argv))
        if not self.responses:
            raise AssertionError(f"unexpected carrier command: {argv}")
        return self.responses.pop(0)


class NoopCarrier(CarrierProviderAdapter):
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id=placement_id, state="UNKNOWN", evidence_ref=None)


class CarrierProviderApiTests(unittest.TestCase):
    def test_package_exports_carrier_provider_adapter(self) -> None:
        self.assertIs(ExportedCarrierProviderAdapter, CarrierProviderAdapter)

    def test_open_accepts_new_carrier_adapter_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = AgentServiceSlice1.open(Path(tmp) / "service.db", carrier_adapter=NoopCarrier())
            service.close()

    def test_open_preserves_host_adapter_compatibility_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = AgentServiceSlice1.open(Path(tmp) / "service.db", host_adapter=NoopCarrier())
            service.close()

    def test_open_rejects_two_provider_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                AgentServiceSlice1.open(
                    Path(tmp) / "service.db",
                    carrier_adapter=NoopCarrier(),
                    host_adapter=NoopCarrier(),
                )


class AgentAutomationCarrierAdapterTests(unittest.TestCase):
    def _revision(self, standing_profile: dict | None = None) -> AgentRevision:
        profile = standing_profile or {
            "kind": "agent-automation-browserless",
            "campaignId": "campaign:agent-service-r4",
            "agentId": "A01",
            "sharedPrompt": "Carry out the assigned work.",
            "roleCard": "You are the verifier.",
        }
        return AgentRevision(
            id="arev_test",
            definition_id="adef_test",
            spec={"carrier": profile},
            created_at_ns=1,
        )

    def _adapter(
        self,
        runner: FakeRunner,
        revision: AgentRevision | None = None,
        *,
        bind: bool = True,
        state_root: Path | None = None,
    ):
        resolved = revision or self._revision()
        if state_root is None:
            temp = tempfile.TemporaryDirectory()
            self.addCleanup(temp.cleanup)
            state_root = Path(temp.name)
        adapter = AgentAutomationCarrierAdapter(
            revision_resolver=lambda revision_id: resolved,
            state_root=state_root,
            command_runner=runner,
            executable=Path("/root/tools/bin/agent-automation"),
        )
        if bind:
            adapter.bind_placement("place-1", resolved.id)
        return adapter

    def test_host_adapter_name_remains_compatibility_alias(self) -> None:
        self.assertIs(HostAdapter, CarrierProviderAdapter)

    def test_observe_maps_bound_census_to_ready(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {
                            "agentId": "A01",
                            "materializationStanding": "bound",
                            "providerResource": "chatgpt://conversation/abc",
                        }
                    ],
                }
            ]
        )
        adapter = self._adapter(runner)

        observation = adapter.observe("place-1")

        self.assertEqual(observation.state, "READY")
        self.assertIn("sha256:", observation.evidence_ref or "")
        self.assertEqual(runner.calls[0][1], "census")

    def test_ensure_unrecorded_materialization_reconciles(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {"agentId": "A01", "materializationStanding": None, "providerResource": None}
                    ],
                },
                {"kind": "ordivon.temporal-materialization-reconcile-admission", "agentId": "A01"},
            ]
        )
        adapter = self._adapter(runner)

        adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census", "reconcile"])
        self.assertIn("--agent-id", runner.calls[1])
        self.assertIn("A01", runner.calls[1])

    def test_ensure_unknown_materialization_reconciles_without_birth(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {"agentId": "A01", "materializationStanding": "unknown", "providerResource": None}
                    ],
                },
                {"kind": "ordivon.temporal-materialization-reconcile-admission", "agentId": "A01"},
            ]
        )
        adapter = self._adapter(runner)

        adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census", "reconcile"])

    def test_ensure_submit_observed_materialization_reconciles_without_birth(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {
                            "agentId": "A01",
                            "materializationStanding": "submit-observed",
                            "providerResource": None,
                        }
                    ],
                },
                {"kind": "ordivon.temporal-materialization-reconcile-admission", "agentId": "A01"},
            ]
        )
        adapter = self._adapter(runner)

        adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census", "reconcile"])

    def test_ensure_pre_effect_failed_reconciles_same_effect_identity(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {
                            "agentId": "A01",
                            "materializationStanding": "pre-effect-failed",
                            "providerResource": None,
                        }
                    ],
                },
                {"kind": "ordivon.temporal-materialization-reconcile-admission", "agentId": "A01"},
            ]
        )
        adapter = self._adapter(runner)

        adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census", "reconcile"])

    def test_ensure_prepared_fails_closed_instead_of_guessing_next_effect(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {
                            "agentId": "A01",
                            "materializationStanding": "prepared",
                            "providerResource": None,
                        }
                    ],
                }
            ]
        )
        adapter = self._adapter(runner)

        with self.assertRaises(CarrierCommandError):
            adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census"])

    def test_retire_fails_closed_when_provider_has_no_retirement_contract(self) -> None:
        adapter = self._adapter(FakeRunner([]))

        with self.assertRaises(CarrierRetireUnsupported):
            adapter.retire("place-1", "ainst-1")

    def test_ensure_bound_is_noop_and_does_not_redispatch(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {
                            "agentId": "A01",
                            "materializationStanding": "bound",
                            "providerResource": "chatgpt://conversation/abc",
                        }
                    ],
                }
            ]
        )
        adapter = self._adapter(runner)

        adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census"])

    def test_ensure_human_required_is_noop_and_does_not_cross_send(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {
                            "agentId": "A01",
                            "materializationStanding": "human-required",
                            "providerResource": None,
                        }
                    ],
                }
            ]
        )
        adapter = self._adapter(runner)

        adapter.ensure("place-1", "ainst-1", "arev_test")

        self.assertEqual([call[1] for call in runner.calls], ["census"])

    def test_observe_preserves_nonready_provider_standing(self) -> None:
        for standing, expected in (
            (None, "UNRECORDED"),
            ("unknown", "AMBIGUOUS"),
            ("submit-observed", "AMBIGUOUS"),
            ("pre-effect-failed", "PRE_EFFECT_FAILED"),
            ("human-required", "HUMAN_REQUIRED"),
        ):
            with self.subTest(standing=standing):
                runner = FakeRunner(
                    [
                        {
                            "campaignId": "campaign:agent-service-r4",
                            "materializations": [
                                {
                                    "agentId": "A01",
                                    "materializationStanding": standing,
                                    "providerResource": None,
                                }
                            ],
                        }
                    ]
                )
                adapter = self._adapter(runner)
                self.assertEqual(adapter.observe("place-1").state, expected)

    def test_profile_is_materialized_as_exact_campaign_spec(self) -> None:
        runner = FakeRunner(
            [
                {
                    "campaignId": "campaign:agent-service-r4",
                    "materializations": [
                        {"agentId": "A01", "materializationStanding": None, "providerResource": None}
                    ],
                }
            ]
        )
        adapter = self._adapter(runner)

        adapter.observe("place-1")

        spec_index = runner.calls[0].index("--spec") + 1
        spec_path = Path(runner.calls[0][spec_index])
        value = json.loads(spec_path.read_text(encoding="utf-8"))
        self.assertEqual(
            value,
            {
                "campaignId": "campaign:agent-service-r4",
                "sharedPrompt": "Carry out the assigned work.",
                "roster": [{"agentId": "A01", "roleCard": "You are the verifier."}],
            },
        )

    def test_placement_binding_survives_adapter_reconstruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp)
            revision = self._revision()
            first = self._adapter(FakeRunner([]), revision, bind=False, state_root=state_root)
            first.bind_placement("place-1", revision.id)

            second_runner = FakeRunner(
                [
                    {
                        "campaignId": "campaign:agent-service-r4",
                        "materializations": [
                            {
                                "agentId": "A01",
                                "materializationStanding": "bound",
                                "providerResource": "chatgpt://conversation/abc",
                            }
                        ],
                    }
                ]
            )
            second = self._adapter(second_runner, revision, bind=False, state_root=state_root)

            self.assertEqual(second.observe("place-1").state, "READY")

    def test_missing_or_wrong_carrier_profile_fails_closed(self) -> None:
        for spec in ({}, {"carrier": {"kind": "other"}}):
            with self.subTest(spec=spec):
                revision = AgentRevision(
                    id="arev_test",
                    definition_id="adef_test",
                    spec=spec,
                    created_at_ns=1,
                )
                adapter = self._adapter(FakeRunner([]), revision, bind=False)
                with self.assertRaises(CarrierProfileError):
                    adapter.bind_placement("place-1", revision.id)


if __name__ == "__main__":
    unittest.main()
