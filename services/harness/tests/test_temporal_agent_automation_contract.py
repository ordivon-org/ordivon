from __future__ import annotations
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TemporalAgentAutomationContractTests(unittest.TestCase):
    def test_worker_registers_current_temporal_workflows(self):
        text = (ROOT / "scripts/temporal_agent_automation.py").read_text()
        for name in (
            "CAMPAIGN_MATERIALIZE_WORKFLOW",
            "MATERIALIZE_WORKFLOW",
            "AGENT_RECONCILE_WORKFLOW",
            "AGENT_CONTINUE_WORKFLOW",
        ):
            self.assertIn(f"@workflow.defn(name={name})", text)
        for retired in (
            "CAMPAIGN_BIRTH_WORKFLOW",
            "CampaignBirthWorkflow",
            "CampaignBirthInput",
            "max_concurrent_births",
            "prompt_file",
        ):
            self.assertNotIn(retired, text)
        tree = ast.parse(text)
        run_worker = next(
            node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_worker"
        )
        worker_call = next(
            node
            for node in ast.walk(run_worker)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Worker"
        )
        workflows = next(kw.value for kw in worker_call.keywords if kw.arg == "workflows")
        self.assertIsInstance(workflows, ast.List)
        self.assertEqual(
            [elt.id for elt in workflows.elts if isinstance(elt, ast.Name)],
            [
                "CampaignMaterializeWorkflow",
                "MaterializeWorkflow",
                "AgentReconcileWorkflow",
                "AgentContinueWorkflow",
            ],
        )

    def test_campaign_materialization_admits_one_durable_parent(self):
        path = ROOT / "scripts/temporal_agent_automation_launch.py"
        text = path.read_text()
        campaign = text[
            text.index('if a.operation == "campaign-materialize":') : text.index(
                'elif a.operation == "materialize":'
            )
        ]
        self.assertNotIn("asyncio.gather(", campaign)
        self.assertIn("CAMPAIGN_MATERIALIZE_WORKFLOW", campaign)
        self.assertIn('"campaign:" + a.campaign_ref.removeprefix("sha256:")', campaign)
        self.assertIn("MaterializationInput(", campaign)
        self.assertIn("WorkflowIDReusePolicy.REJECT_DUPLICATE", text)
        self.assertIn("WorkflowIDConflictPolicy.USE_EXISTING", text)
        self.assertIn("except WorkflowAlreadyStartedError as error:", text)
        self.assertIn('"disposition": "existing"', text)

    def test_failed_continue_retry_uses_temporal_native_workflow_id_arbitration(self):
        """Execute the real launcher functions, not a source-text assertion."""
        import asyncio
        from enum import Enum
        from types import SimpleNamespace

        path = ROOT / "scripts/temporal_agent_automation_launch.py"
        tree = ast.parse(path.read_text())
        functions = [
            n for n in tree.body
            if isinstance(n, ast.AsyncFunctionDef)
            and n.name in {"_admit_workflow", "_admit_failed_continue_retry"}
        ]
        self.assertEqual(len(functions), 2)

        class AlreadyStarted(Exception):
            run_id = "prior-existing"

        values = SimpleNamespace(
            REJECT_DUPLICATE="reject_duplicate",
            ALLOW_DUPLICATE_FAILED_ONLY="allow_duplicate_failed_only",
        )
        statuses = Enum("TemporalStatus", ["FAILED", "COMPLETED"])
        ns = {
            "Client": object, "AgentContinueInput": object,
            "WorkflowIDReusePolicy": values,
            "WorkflowIDConflictPolicy": SimpleNamespace(USE_EXISTING="use_existing"),
            "WorkflowExecutionStatus": statuses,
            "WorkflowAlreadyStartedError": AlreadyStarted,
            "AGENT_CONTINUE_WORKFLOW": "continue",
        }
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), ns)

        class Client:
            def __init__(self):
                self.status = statuses.FAILED
                self.starts = []

            def get_workflow_handle(self, workflow_id):
                assert workflow_id == "logical-turn"
                async def describe():
                    return SimpleNamespace(status=self.status, run_id="failed-run-1")
                return SimpleNamespace(describe=describe)

            async def start_workflow(self, workflow, value, **kwargs):
                self.starts.append(kwargs)
                return SimpleNamespace(id=kwargs["id"])

        async def scenarios():
            client = Client()
            normal = await ns["_admit_workflow"](
                client, "continue", object(),
                workflow_id="logical-turn", task_queue="queue",
            )
            self.assertEqual(normal["disposition"], "admitted")
            self.assertEqual(
                client.starts[-1]["id_reuse_policy"], values.REJECT_DUPLICATE,
            )

            # Concurrent callers converge on the same native server-owned key;
            # this test asserts our request contract, not the server's internals.
            responses = await asyncio.gather(*(
                ns["_admit_failed_continue_retry"](
                    client, object(),
                    logical_workflow_id="logical-turn", task_queue="queue",
                )
                for _ in range(2)
            ))
            self.assertEqual(
                [item["workflowId"] for item in responses],
                ["logical-turn", "logical-turn"],
            )
            self.assertTrue(all("retryId" not in item for item in responses))
            self.assertTrue(all(
                item["logicalWorkflowId"] == "logical-turn"
                for item in responses
            ))
            self.assertEqual(len(client.starts), 3)
            for request in client.starts[1:]:
                self.assertEqual(request["id"], "logical-turn")
                self.assertEqual(
                    request["id_reuse_policy"], values.ALLOW_DUPLICATE_FAILED_ONLY,
                )
                self.assertEqual(
                    request["id_conflict_policy"], "use_existing",
                )

            client.status = statuses.COMPLETED
            refused = await ns["_admit_failed_continue_retry"](
                client, object(),
                logical_workflow_id="logical-turn", task_queue="queue",
            )
            self.assertEqual(refused["disposition"], "existing")
            self.assertIn("not-admitted-prior", refused["retryStanding"])
            self.assertEqual(len(client.starts), 3)

        asyncio.run(scenarios())

    def test_effect_workflows_are_deterministic_shells_around_activities(self):
        path = ROOT / "scripts/temporal_agent_automation.py"
        text = path.read_text()
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in {
                "OccurrenceMaterializeWorkflow",
                "AgentReconcileWorkflow",
                "AgentHumanResumeWorkflow",
                "AgentContinueWorkflow",
            }:
                segment = ast.get_source_segment(text, node) or ""
                self.assertNotIn("subprocess.", segment)
                self.assertNotIn("playwright", segment.lower())
                self.assertNotIn("BrowserlessAutomationService(", segment)
        self.assertIn("retry_policy=EFFECT_FENCED_RETRY", text)

    def test_activity_provider_effects_reenter_current_config_each_time(self):
        text = (ROOT / "scripts/temporal_agent_automation.py").read_text()
        segment = text[
            text.index("class BrowserlessActivities:") : text.index("EFFECT_FENCED_RETRY =")
        ]
        self.assertIn("self.config_path = config_path.resolve()", segment)
        self.assertIn(
            "return BrowserlessAutomationConfig.from_dict(_read_json(self.config_path))", segment
        )
        self.assertNotIn("self.effects =", segment)
        self.assertIn("with self._endpoint_lock(endpoint_id):", segment)
        self.assertIn("with _carrier_lease(candidate, endpoint_id, blocking=True):", segment)

    def test_only_narrow_transport_pre_effect_failures_auto_retry(self):
        path = ROOT / "scripts/temporal_agent_automation.py"
        tree = ast.parse(path.read_text())
        cls = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "BrowserlessActivities"
        )
        fn = next(
            n
            for n in cls.body
            if isinstance(n, ast.FunctionDef) and n.name == "_pre_effect_auto_retryable"
        )
        fn.decorator_list = []
        ns = {}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), ns)
        retryable = ns["_pre_effect_auto_retryable"]
        self.assertTrue(
            retryable("Browserless/ChatGPT blocked before SEND: browserless-connect:TimeoutError")
        )
        self.assertTrue(
            retryable("Browserless/ChatGPT blocked before SEND: provider-navigation:TimeoutError")
        )
        for detail in (
            "Browserless/ChatGPT blocked before SEND: conversation-history-rate-limit-modal",
            "Browserless/ChatGPT blocked before SEND: composer-not-empty",
            "Browserless/ChatGPT blocked before SEND: already-generating",
            None,
        ):
            self.assertFalse(retryable(detail), detail)

    def test_temporal_sdk_is_pinned(self):
        self.assertEqual(
            (ROOT / "config/agent-automation-temporal-requirements.txt").read_text().splitlines(),
            [
                "temporalio==1.34.0",
                "rfc8785==0.1.4",
                "mcp==2.3.0",
                "httpx==0.28.1",
                "psycopg==3.3.6",
            ],
        )


if __name__ == "__main__":
    unittest.main()


class TemporalCampaignParentStandardTests(unittest.TestCase):
    def test_campaign_fanout_is_owned_by_temporal_parent_child_workflows(self):
        worker = (ROOT / "scripts/temporal_agent_automation.py").read_text()
        launcher = (ROOT / "scripts/temporal_agent_automation_launch.py").read_text()
        self.assertIn("CAMPAIGN_MATERIALIZE_WORKFLOW", worker)
        self.assertIn("class CampaignMaterializeWorkflow", worker)
        self.assertIn("workflow.start_child_workflow(", worker)
        self.assertIn("id=value.effect_id", worker.replace(" ", ""))
        self.assertNotIn("OccurrenceInput", worker)
        self.assertNotIn("OccurrenceMaterializeWorkflow", worker)

        campaign = launcher[
            launcher.index('if a.operation == "campaign-materialize":') : launcher.index(
                'elif a.operation == "materialize":'
            )
        ]
        self.assertNotIn("asyncio.gather(", campaign)
        self.assertIn("CAMPAIGN_MATERIALIZE_WORKFLOW", campaign)
        self.assertIn("campaign_ref", campaign)


class ExplicitMaterializationCarrierTests(unittest.TestCase):
    def test_materialization_input_freezes_explicit_carrier(self):
        text = (ROOT / 'scripts/temporal_agent_automation.py').read_text()
        self.assertIn('carrier: str = "browserless"', text)
        self.assertIn('{"browserless", "windows-user-browser"}', text)
        self.assertNotIn('"automatic-failover"', text)

    def test_windows_user_browser_is_explicit_not_browserless_failover(self):
        text = (ROOT / 'scripts/temporal_agent_automation.py').read_text()
        self.assertIn('value.carrier == "windows-user-browser"', text)
        self.assertIn('materialize_user_browser(', text)
        launcher = (ROOT / 'scripts/temporal_agent_automation_launch.py').read_text()
        self.assertIn('--carrier', launcher)
        self.assertIn('choices=("browserless", "windows-user-browser")', launcher)
