from __future__ import annotations

import unittest

from ordivon_harness.dap_provider_port import (
    DEBUGGER_CONFIGURATION,
    EFFECT_CAPABLE,
    EXECUTION_CONTROL,
    OBSERVATION,
    PROCESS_LIFECYCLE,
    TARGET_MUTATION,
    DapActionIntent,
    DapActionObservation,
    DapProviderIdentity,
    DapProviderReady,
    DapStopEpoch,
    DapTargetBinding,
    DapTransientHandle,
    HarnessDapProviderPort,
    admitted_dap_actions,
    dap_action_consequence,
)

DIGEST = "sha256:" + "1" * 64


def binding() -> DapTargetBinding:
    return DapTargetBinding(
        session_id="dap-session:test",
        target_ref="binary:fixture",
        process_owner="dap-provider",
        effect_executor="dap-provider",
    )


def stop(epoch: int = 1) -> DapStopEpoch:
    return DapStopEpoch(
        session_id="dap-session:test",
        epoch=epoch,
        thread_id=1,
        reason="breakpoint",
        all_threads_stopped=True,
    )


class FakeProvider:
    async def initialize(self) -> DapProviderReady:
        return DapProviderReady(
            identity=DapProviderIdentity("dap:test", "fixture", "1"),
            supported_actions=("threads",),
            raw_capabilities={},
        )

    async def execute(self, intent: DapActionIntent) -> DapActionObservation:
        return DapActionObservation(
            intent_digest=intent.digest,
            action=intent.action,
            consequence=intent.consequence,
            response={"threads": []},
            events=(),
            effect_executor="none",
        )

    async def shutdown(self) -> None:
        return None


class DapProviderPortTests(unittest.TestCase):
    def test_consequence_table_separates_observation_control_mutation_and_lifecycle(self) -> None:
        expected = {
            "threads": OBSERVATION,
            "variables": OBSERVATION,
            "readMemory": OBSERVATION,
            "continue": EXECUTION_CONTROL,
            "pause": EXECUTION_CONTROL,
            "setBreakpoints": DEBUGGER_CONFIGURATION,
            "setVariable": TARGET_MUTATION,
            "writeMemory": TARGET_MUTATION,
            "launch": PROCESS_LIFECYCLE,
            "terminate": PROCESS_LIFECYCLE,
            "evaluate": EFFECT_CAPABLE,
        }
        for action, consequence in expected.items():
            with self.subTest(action=action):
                self.assertEqual(dap_action_consequence(action), consequence)

    def test_evaluate_is_never_classified_as_observation(self) -> None:
        self.assertEqual(dap_action_consequence("evaluate"), EFFECT_CAPABLE)
        self.assertNotEqual(dap_action_consequence("evaluate"), OBSERVATION)

    def test_raw_custom_request_is_not_in_harness_action_surface(self) -> None:
        self.assertNotIn("customRequest", admitted_dap_actions())
        with self.assertRaisesRegex(ValueError, "not admitted"):
            dap_action_consequence("customRequest")

    def test_stop_scoped_actions_require_exact_stop_digest(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires exact stop digest"):
            DapActionIntent(
                session_id="dap-session:test",
                target_binding_digest=binding().digest,
                action="variables",
                arguments={"variablesReference": 1},
            )
        intent = DapActionIntent(
            session_id="dap-session:test",
            target_binding_digest=binding().digest,
            action="variables",
            arguments={"variablesReference": 1},
            stop_digest=stop().digest,
        )
        self.assertEqual(intent.consequence, OBSERVATION)

    def test_transient_handles_are_invalid_after_new_stop_epoch(self) -> None:
        first = stop(1)
        second = stop(2)
        frame = DapTransientHandle(first.digest, "frame", 0)
        frame.require_stop(first)
        with self.assertRaisesRegex(ValueError, "different stopped epoch"):
            frame.require_stop(second)

    def test_target_process_owner_and_effect_executor_are_explicit(self) -> None:
        target = binding()
        self.assertEqual(target.process_owner, "dap-provider")
        self.assertEqual(target.effect_executor, "dap-provider")
        with self.assertRaisesRegex(ValueError, "process owner"):
            DapTargetBinding(
                "dap-session:test",
                "binary:fixture",
                "implicit",
                "dap-provider",
            )

    def test_observation_result_cannot_claim_physical_effect_executor(self) -> None:
        intent = DapActionIntent(
            session_id="dap-session:test",
            target_binding_digest=binding().digest,
            action="threads",
            arguments={},
        )
        DapActionObservation(
            intent.digest,
            "threads",
            OBSERVATION,
            {"threads": []},
            (),
            "none",
        )
        with self.assertRaisesRegex(ValueError, "cannot claim an effect executor"):
            DapActionObservation(
                intent.digest,
                "threads",
                OBSERVATION,
                {"threads": []},
                (),
                "dap-provider",
            )

    def test_effectful_result_requires_physical_effect_executor(self) -> None:
        intent = DapActionIntent(
            session_id="dap-session:test",
            target_binding_digest=binding().digest,
            action="continue",
            arguments={"threadId": 1},
            stop_digest=stop().digest,
        )
        with self.assertRaisesRegex(ValueError, "must identify"):
            DapActionObservation(
                intent.digest,
                "continue",
                EXECUTION_CONTROL,
                {"allThreadsContinued": True},
                (),
                "none",
            )

    def test_provider_ready_is_descriptor_not_authority(self) -> None:
        ready = DapProviderReady(
            identity=DapProviderIdentity("dap:gdb", "gdb", "17.2"),
            supported_actions=("continue", "threads"),
            raw_capabilities={"supportsWriteMemoryRequest": True},
        )
        self.assertTrue(ready.digest.startswith("sha256:"))
        self.assertEqual(ready.raw_capabilities["supportsWriteMemoryRequest"], True)
        self.assertEqual(dap_action_consequence("threads"), OBSERVATION)
        self.assertEqual(dap_action_consequence("writeMemory"), TARGET_MUTATION)

    def test_port_has_no_unclassified_raw_request_escape_hatch(self) -> None:
        provider = FakeProvider()
        self.assertIsInstance(provider, HarnessDapProviderPort)
        for name in ("raw_request", "custom_request", "send", "write_memory"):
            self.assertFalse(hasattr(HarnessDapProviderPort, name))


if __name__ == "__main__":
    unittest.main()
