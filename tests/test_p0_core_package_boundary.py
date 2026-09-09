from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HarnessCorePackageBoundaryTests(unittest.TestCase):
    def run_probe(self, statement: str) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-c", statement],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_package_root_and_api_do_not_eagerly_load_host(self) -> None:
        observed = self.run_probe(
            "import json,sys,ordivon_harness; "
            "root_loaded=any(k=='ordivon_host' or k.startswith('ordivon_host.') for k in sys.modules); "
            "import ordivon_harness.api as api; "
            "api_loaded=any(k=='ordivon_host' or k.startswith('ordivon_host.') for k in sys.modules); "
            "print(json.dumps({'rootLoadedHost':root_loaded,'apiLoadedHost':api_loaded,"
            "'hasStandalone':'StandaloneHarnessRunner' in api.__all__,"
            "'hasSqliteStore':'SQLiteHarnessStore' in api.__all__,"
            "'hasProviderCodec':'HarnessProviderCallRecordV4' in api.__all__}))"
        )
        self.assertFalse(observed["rootLoadedHost"])
        self.assertFalse(observed["apiLoadedHost"])
        self.assertFalse(observed["hasStandalone"])
        self.assertFalse(observed["hasSqliteStore"])
        self.assertFalse(observed["hasProviderCodec"])

    def test_retired_atlas_first_look_runtime_bridge_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'atlasBridgeSpec':importlib.util.find_spec('ordivon_harness.ordivon.atlas_first_look_runtime_bridge') is not None}))"
        )
        self.assertFalse(observed["atlasBridgeSpec"])

    def test_retired_repository_repair_trial_bridge_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'repositoryRepairBridgeSpec':importlib.util.find_spec('ordivon_harness.ordivon.sqlite_repository_repair_bridge') is not None}))"
        )
        self.assertFalse(observed["repositoryRepairBridgeSpec"])

    def test_retired_interaction_context_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'interactionContext':importlib.util.find_spec('ordivon_harness.interaction_context') is not None}))"
        )
        self.assertFalse(observed["interactionContext"])

    def test_retired_cli_capabilities_surface_is_absent(self) -> None:
        from ordivon_harness.cli import build_parser
        help_text = build_parser().format_help()
        self.assertNotIn("capabilities", help_text)
        import ordivon_harness.independent_cli as independent_cli
        self.assertFalse(hasattr(independent_cli, "capabilities"))

    def test_internal_ordivon_package_has_no_lazy_aggregation_facade(self) -> None:
        import ordivon_harness.ordivon as implementation_package

        self.assertEqual(implementation_package.__all__, [])
        self.assertNotIn("_EXPORTS", implementation_package.__dict__)
        self.assertNotIn("__getattr__", implementation_package.__dict__)

    def test_retired_standalone_tool_bridge_protocol_is_absent(self) -> None:
        from ordivon_harness import standalone

        self.assertFalse(hasattr(standalone, "StandaloneToolBridge"))

    def test_retired_native_run_recovery_assessment_surface_is_absent(self) -> None:
        from ordivon_harness.cli import build_parser

        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'recoveryModule':importlib.util.find_spec('ordivon_harness.recovery') is not None}))"
        )
        self.assertFalse(observed["recoveryModule"])
        parser = build_parser()
        command_choices = next(
            action.choices
            for action in parser._actions
            if action.dest == "command" and isinstance(action.choices, dict)
        )
        self.assertNotIn("recover", command_choices)

    def test_retired_tool_program_durable_recovery_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'toolProgramDurableRecovery':importlib.util.find_spec('ordivon_harness.tool_program_durable_recovery') is not None}))"
        )
        self.assertFalse(observed["toolProgramDurableRecovery"])

    def test_retired_telemetry_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'telemetry':importlib.util.find_spec('ordivon_harness.telemetry') is not None}))"
        )
        self.assertFalse(observed["telemetry"])

    def test_retired_provider_use_policy_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'providerUsePolicy':importlib.util.find_spec('ordivon_harness.provider_use_policy') is not None}))"
        )
        self.assertFalse(observed["providerUsePolicy"])

    def test_retired_observation_tool_surface_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'observationToolSurface':importlib.util.find_spec('ordivon_harness.observation_tool_surface') is not None}))"
        )
        self.assertFalse(observed["observationToolSurface"])

    def test_retired_loop_driver_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'loopDriver':importlib.util.find_spec('ordivon_harness.loop_driver') is not None}))"
        )
        self.assertFalse(observed["loopDriver"])

    def test_retired_mandate_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'mandate':importlib.util.find_spec('ordivon_harness.mandate') is not None}))"
        )
        self.assertFalse(observed["mandate"])

    def test_retired_claim_standing_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'claimStanding':importlib.util.find_spec('ordivon_harness.claim_standing') is not None}))"
        )
        self.assertFalse(observed["claimStanding"])

    def test_retired_finance_runtime_bridge_modules_are_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "mods=('ordivon_harness.ordivon.finance_observe_runtime_bridge','ordivon_harness.ordivon.finance_research_runtime_bridge'); "
            "print(json.dumps({m:importlib.util.find_spec(m) is not None for m in mods}))"
        )
        self.assertTrue(all(value is False for value in observed.values()))

    def test_retired_projected_no_tool_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'projectedNoToolSpec':importlib.util.find_spec('ordivon_harness.projected_no_tool') is not None}))"
        )
        self.assertFalse(observed["projectedNoToolSpec"])

    def test_retired_observation_export_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'observationExportSpec':importlib.util.find_spec('ordivon_harness.observation_export') is not None}))"
        )
        self.assertFalse(observed["observationExportSpec"])

    def test_retired_subprocess_lifecycle_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'subprocessLifecycleSpec':importlib.util.find_spec('ordivon_harness.subprocess_lifecycle') is not None}))"
        )
        self.assertFalse(observed["subprocessLifecycleSpec"])

    def test_retired_tool_semantics_module_is_absent(self) -> None:
        observed = self.run_probe(
            "import importlib.util,json; "
            "print(json.dumps({'toolSemanticsSpec':importlib.util.find_spec('ordivon_harness.tool_semantics') is not None}))"
        )
        self.assertFalse(observed["toolSemanticsSpec"])

    def test_package_root_has_no_host_compatibility_exports(self) -> None:
        observed = self.run_probe(
            "import json,sys,ordivon_harness; "
            "names=dir(ordivon_harness); "
            "print(json.dumps({'hasHostRunner':'HarnessRunner' in names,"
            "'hasRunContract':'HarnessRunContract' in names,"
            "'hostLoaded':any(k=='ordivon_host' or k.startswith('ordivon_host.') for k in sys.modules)}))"
        )
        self.assertFalse(observed["hasHostRunner"])
        self.assertFalse(observed["hasRunContract"])
        self.assertFalse(observed["hostLoaded"])
        self.assertFalse((ROOT / "src" / "ordivon_harness" / "core.py").exists())

    def test_independent_modules_have_no_host_compatibility_imports(self) -> None:
        package = ROOT / "src" / "ordivon_harness"
        paths = (
            "run_state.py",
            "standalone.py",
            "independent_result.py",
            "independent_cli.py",
            "ordivon/tool_bridge.py",
            "ordivon/loop.py",
            "ordivon/run_recovery.py",
            "ordivon/runtime_lowering.py",
            "ordivon/sqlite_agent_bridge.py",
            "ordivon/sqlite_run_store.py",
            "ordivon/sqlite_runtime_bridge.py",
        )
        for relative in paths:
            with self.subTest(relative=relative):
                source = (package / relative).read_text(encoding="utf-8")
                self.assertNotIn("ordivon_host", source)
                self.assertNotIn("_host_compat", source)


if __name__ == "__main__":
    unittest.main()
