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
            "AGENT_HUMAN_RESUME_WORKFLOW",
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
            node for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_worker"
        )
        worker_call = next(
            node for node in ast.walk(run_worker)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Worker"
        )
        workflows = next(kw.value for kw in worker_call.keywords if kw.arg == "workflows")
        self.assertIsInstance(workflows, ast.List)
        self.assertEqual(
            [elt.id for elt in workflows.elts if isinstance(elt, ast.Name)],
            ["CampaignMaterializeWorkflow", "MaterializeWorkflow", "AgentReconcileWorkflow", "AgentHumanResumeWorkflow", "AgentContinueWorkflow"],
        )

    def test_campaign_materialization_admits_one_durable_parent(self):
        path = ROOT / "scripts/temporal_agent_automation_launch.py"
        text = path.read_text()
        campaign = text[
            text.index('if a.operation == "campaign-materialize":'):
            text.index('elif a.operation == "materialize":')
        ]
        self.assertNotIn("asyncio.gather(", campaign)
        self.assertIn("CAMPAIGN_MATERIALIZE_WORKFLOW", campaign)
        self.assertIn('"campaign:" + a.campaign_ref.removeprefix("sha256:")', campaign)
        self.assertIn("MaterializationInput(", campaign)
        self.assertIn("WorkflowIDReusePolicy.REJECT_DUPLICATE", text)
        self.assertIn("WorkflowIDConflictPolicy.USE_EXISTING", text)
        self.assertIn("except WorkflowAlreadyStartedError as error:", text)
        self.assertIn('"disposition": "existing"', text)

    def test_failed_continue_retry_preserves_logical_turn_and_uses_fresh_execution_identity(self):
        path = ROOT / "scripts/temporal_agent_automation_launch.py"
        text = path.read_text()
        tree = ast.parse(text)
        retry_fn = next(
            node for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_admit_failed_continue_retry"
        )
        uuid7_call = next(
            node for node in ast.walk(retry_fn)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "uuid"
            and node.func.attr == "uuid7"
        )
        self.assertIsNotNone(uuid7_call)
        retry_segment = ast.get_source_segment(text, retry_fn) or ""
        self.assertIn("WorkflowExecutionStatus.FAILED", retry_segment)
        self.assertIn('"retryStanding": "admitted-after-failed"', retry_segment)
        self.assertIn('"logicalWorkflowId": logical_workflow_id', retry_segment)
        self.assertIn("logical_workflow_id=turn_request_id", text.replace(" ", ""))
        self.assertIn("turn_request_id=turn_request_id", text.replace(" ", ""))
        self.assertIn('a.operation == "continue-retry"', text)
        self.assertIn('"continue-retry"', text)

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
            ["temporalio==1.32.0", "rfc8785==0.1.4"],
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
            launcher.index('if a.operation == "campaign-materialize":'):
            launcher.index('elif a.operation == "materialize":')
        ]
        self.assertNotIn("asyncio.gather(", campaign)
        self.assertIn("CAMPAIGN_MATERIALIZE_WORKFLOW", campaign)
        self.assertIn("campaign_ref", campaign)
