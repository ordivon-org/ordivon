#!/usr/bin/env python3
"""Temporal workflows and activities for Browserless-backed Agent Automation.

Temporal owns durable workflow execution, child-workflow fan-out, retries, timers and worker
recovery. Browserless owns browser lifecycle. The Browserless adapter's effect ledger remains the
narrow fence for ChatGPT Web's non-idempotent SEND boundary.
"""

from __future__ import annotations

import concurrent.futures
import threading
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from agent_automation_browserless import (
        BrowserlessAutomationConfig,
        BrowserlessAutomationHold,
        BrowserlessAutomationService,
        diagnose_provider_preflight,
        _carrier_lease,
        _read_json,
    )
    from agent_automation_browserless_effects import BrowserlessEffectAdapter
    from campaign_materialization import campaign_census


MATERIALIZE_ACTIVITY = "ordivon.browserless.materialize"
RECONCILE_ACTIVITY = "ordivon.browserless.reconcile"
HUMAN_RESUME_ACTIVITY = "ordivon.browserless.human-resume"
CONTINUE_ACTIVITY = "ordivon.browserless.continue"
OCCURRENCE_MATERIALIZE_WORKFLOW = "ordivon.occurrence.materialize"
AGENT_RECONCILE_WORKFLOW = "ordivon.agent.reconcile"
AGENT_HUMAN_RESUME_WORKFLOW = "ordivon.agent.human-resume"
AGENT_CONTINUE_WORKFLOW = "ordivon.agent.continue"


@dataclass(frozen=True)
class OccurrenceInput:
    spec_path: str
    agent_id: str


@dataclass(frozen=True)
class AgentContinueInput:
    spec_path: str
    agent_id: str
    turn_request_id: str
    prompt: str


class BrowserlessActivities:
    def __init__(self, config_path: Path) -> None:
        # Worker lifetime is deliberately longer than Browserless/network carrier generations.
        # Retain only the config authority path; never retain endpoint identities or exec prefixes
        # across activities. Every provider-effect activity re-enters the current config bytes.
        self.config_path = config_path.resolve()
        startup_config = self._current_config()
        self.provider_concurrency = max(1, len(startup_config.browserless_pool.endpoints))
        self._endpoint_locks_guard = threading.Lock()
        self._endpoint_locks: dict[str, threading.Lock] = {}

    def _current_config(self) -> BrowserlessAutomationConfig:
        return BrowserlessAutomationConfig.from_dict(_read_json(self.config_path))

    def _effects(
        self, config: BrowserlessAutomationConfig | None = None
    ) -> BrowserlessEffectAdapter:
        return BrowserlessEffectAdapter(self._current_config() if config is None else config)

    def _endpoint_lock(self, endpoint_id: str) -> threading.Lock:
        with self._endpoint_locks_guard:
            lock = self._endpoint_locks.get(endpoint_id)
            if lock is None:
                lock = threading.Lock()
                self._endpoint_locks[endpoint_id] = lock
            return lock

    @staticmethod
    def _materialization_endpoint_id(config: BrowserlessAutomationConfig, value: OccurrenceInput) -> str:
        context = BrowserlessAutomationService(config)
        spec = context.load_spec(Path(value.spec_path))
        materialization = context._materialization(spec, value.agent_id)
        census = campaign_census(spec, config.ledger)
        row = next(item for item in census["occurrences"] if item["agentId"] == value.agent_id)
        standing = row.get("materializationStanding")
        # Once SEND may have happened, reconciliation must stay on the exact bound carrier. A
        # proven PRE_EFFECT_FAILED attempt is different: no SEND occurred, so stale binding bytes
        # must not be validated before current deterministic routing is selected again.
        if standing in {"unknown", "submit-observed"}:
            binding, _ = context._reconciliation_binding(materialization)
            if binding is not None:
                return str(binding["endpointId"])
            return None
        if standing == "human-required":
            binding = context._current_binding(materialization)
            if binding is not None:
                return str(binding["endpointId"])
        return config.browserless_pool.select(materialization.effect_id).endpoint_id

    @staticmethod
    def _continue_endpoint_id(
        config: BrowserlessAutomationConfig, value: AgentContinueInput
    ) -> str | None:
        context = BrowserlessAutomationService(config)
        spec = context.load_spec(Path(value.spec_path))
        census = campaign_census(spec, config.ledger)
        row = next(item for item in census["occurrences"] if item["agentId"] == value.agent_id)
        if row.get("materializationStanding") != "bound" or not row.get("providerResource"):
            return None
        materialization = context._materialization(spec, value.agent_id)
        binding = context._current_binding(materialization)
        return str(binding["endpointId"]) if binding is not None else None

    def _run_serialized(self, value, endpoint_resolver, effect_call):
        # Hash routing can place several concurrent Temporal activities on one Browserless profile.
        # Browserless health is pool-wide, but the profile itself is a single UI authority surface.
        # Lock per endpoint so different carriers remain parallel while one profile never receives
        # overlapping provider effects. Re-read config after acquiring the lock so waiting cannot
        # resurrect stale endpoint identity/exec-prefix state.
        for _ in range(8):
            candidate = self._current_config()
            endpoint_id = endpoint_resolver(candidate, value)
            if endpoint_id is None:
                return effect_call(self._effects(candidate))
            with self._endpoint_lock(endpoint_id):
                # Cross-process lease also excludes CLI/MCP provider diagnostics from this same
                # persistent profile while the provider effect is in flight.
                with _carrier_lease(candidate, endpoint_id, blocking=True):
                    current = self._current_config()
                    if endpoint_resolver(current, value) != endpoint_id:
                        continue
                    return effect_call(self._effects(current))
        raise RuntimeError(
            "Browserless carrier routing changed repeatedly while waiting for endpoint serialization"
        )

    def _run_materialization_failover(self, value: OccurrenceInput) -> dict:
        # New/proven-pre-effect Materializations may move only across physically/provider-unavailable carriers.
        # Every provider preflight and the subsequent binding/SEND attempt happen under the same
        # cross-process carrier lease. Once an effect has a post-SEND/ambiguous standing, normal
        # bound-carrier reconciliation is used instead and failover is forbidden.
        for _ in range(8):
            candidate = self._current_config()
            context = BrowserlessAutomationService(candidate)
            spec = context.load_spec(Path(value.spec_path))
            materialization = context._materialization(spec, value.agent_id)
            census = campaign_census(spec, candidate.ledger)
            row = next(item for item in census["occurrences"] if item["agentId"] == value.agent_id)
            standing = row.get("materializationStanding")
            if standing in {
                "unknown",
                "submit-observed",
                "human-required",
                "bound",
                "ready-confirmed",
            }:
                return self._run_serialized(
                    value,
                    self._materialization_endpoint_id,
                    lambda effects: effects.materialize(
                        Path(value.spec_path), value.agent_id
                    ),
                )
            saw_current_candidate = False
            rejected: list[str] = []
            for endpoint in candidate.browserless_pool.candidates(materialization.effect_id):
                endpoint_id = endpoint.endpoint_id
                with self._endpoint_lock(endpoint_id):
                    with _carrier_lease(candidate, endpoint_id, blocking=True):
                        current = self._current_config()
                        current_context = BrowserlessAutomationService(current)
                        current_spec = current_context.load_spec(Path(value.spec_path))
                        current_birth = current_context._materialization(current_spec, value.agent_id)
                        current_ids = [
                            row.endpoint_id
                            for row in current.browserless_pool.candidates(current_birth.effect_id)
                        ]
                        if endpoint_id not in current_ids:
                            continue
                        saw_current_candidate = True
                        observation = current_context._provider_preflight_under_carrier_lease(
                            endpoint_id
                        )
                        diagnosis = diagnose_provider_preflight(observation)
                        if diagnosis["carrierRouting"] == "FAILOVER_ALLOWED":
                            rejected.append(f"{endpoint_id}:{observation.get('standing')}")
                            continue
                        return self._effects(current).materialize(
                            Path(value.spec_path),
                            value.agent_id,
                            endpoint_id=endpoint_id,
                            provider_preflight=observation,
                        )
            if saw_current_candidate:
                raise BrowserlessAutomationHold(
                    "provider materialization HOLD: every candidate carrier was unavailable/busy before SEND: "
                    + ", ".join(rejected)
                )
        raise RuntimeError(
            "Browserless materialization carrier set changed repeatedly while waiting for serialization"
        )

    @staticmethod
    def _pre_effect_auto_retryable(detail: str | None) -> bool:
        # PRE_EFFECT_FAILED proves SEND was not crossed, but that is only a safety fact: it does not
        # mean an immediate retry is operationally wise. Auto-retry only narrow transport/navigation
        # timeouts. Provider/UI/profile-state blockers stay durably PRE_EFFECT_FAILED for a future
        # fresh re-entry after the relevant condition has changed.
        value = (detail or "").lower()
        return any(
            marker in value
            for marker in (
                "browserless-connect:timeouterror",
                "provider-navigation:timeouterror",
            )
        )

    @activity.defn(name=MATERIALIZE_ACTIVITY)
    def materialize(self, value: OccurrenceInput) -> dict:
        result = self._run_materialization_failover(value)
        receipt = result.get("receipt") if isinstance(result, dict) else None
        if isinstance(receipt, dict) and receipt.get("standing") == "pre-effect-failed":
            # The durable receipt proves SEND was not crossed. Transport/navigation failures may
            # use Temporal's bounded retry, but explicit provider pressure must not create a
            # thundering herd. It remains safely re-enterable through a later fresh preflight.
            detail = receipt.get("detail")
            if self._pre_effect_auto_retryable(detail):
                raise RuntimeError(
                    f"retryable provider pre-effect failure: {detail or 'unspecified'}"
                )
        return result

    @activity.defn(name=RECONCILE_ACTIVITY)
    def reconcile(self, value: OccurrenceInput) -> dict:
        return self._run_serialized(
            value,
            self._materialization_endpoint_id,
            lambda effects: effects.reconcile(Path(value.spec_path), value.agent_id),
        )

    @activity.defn(name=HUMAN_RESUME_ACTIVITY)
    def human_resume(self, value: OccurrenceInput) -> dict:
        return self._run_serialized(
            value,
            self._materialization_endpoint_id,
            lambda effects: effects.resume_after_human(Path(value.spec_path), value.agent_id),
        )

    @activity.defn(name=CONTINUE_ACTIVITY)
    def continue_turn(self, value: AgentContinueInput) -> dict:
        return self._run_serialized(
            value,
            self._continue_endpoint_id,
            lambda effects: effects.send_turn(
                Path(value.spec_path),
                value.agent_id,
                turn_request_id=value.turn_request_id,
                prompt=value.prompt,
            ),
        )


EFFECT_FENCED_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
)


@workflow.defn(name=OCCURRENCE_MATERIALIZE_WORKFLOW)
class OccurrenceMaterializeWorkflow:
    @workflow.run
    async def run(self, value: OccurrenceInput) -> dict:
        # Activity retry is safe only because the adapter durably claims the exact materialization request identity
        # before SEND. A retry re-enters/reconciles that same effect identity; it cannot blind-send.
        return await workflow.execute_activity(
            MATERIALIZE_ACTIVITY,
            value,
            result_type=dict,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=EFFECT_FENCED_RETRY,
        )


@workflow.defn(name=AGENT_RECONCILE_WORKFLOW)
class AgentReconcileWorkflow:
    @workflow.run
    async def run(self, value: OccurrenceInput) -> dict:
        # Reconcile observes the same already-claimed materialization effect. It may update standing/evidence,
        # but it never authorizes a new provider SEND or increments effect generation.
        return await workflow.execute_activity(
            RECONCILE_ACTIVITY,
            value,
            result_type=dict,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=EFFECT_FENCED_RETRY,
        )


@workflow.defn(name=AGENT_HUMAN_RESUME_WORKFLOW)
class AgentHumanResumeWorkflow:
    @workflow.run
    async def run(self, value: OccurrenceInput) -> dict:
        # HUMAN_REQUIRED proves no prompt SEND has occurred. The materializer atomically claims the
        # same effect identity before READY revalidation/SEND; activity retry reconciles UNKNOWN.
        return await workflow.execute_activity(
            HUMAN_RESUME_ACTIVITY,
            value,
            result_type=dict,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=EFFECT_FENCED_RETRY,
        )


@workflow.defn(name=AGENT_CONTINUE_WORKFLOW)
class AgentContinueWorkflow:
    @workflow.run
    async def run(self, value: AgentContinueInput) -> dict:
        # turnRequestId is durably claimed by the continuation ledger immediately before SEND.
        # Activity retry therefore re-enters the same turn effect identity rather than duplicating it.
        return await workflow.execute_activity(
            CONTINUE_ACTIVITY,
            value,
            result_type=dict,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=EFFECT_FENCED_RETRY,
        )


async def run_worker(
    *, temporal_address: str, namespace: str, task_queue: str, config_path: Path
) -> None:
    client = await Client.connect(temporal_address, namespace=namespace)
    activities = BrowserlessActivities(config_path)
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=activities.provider_concurrency
    ) as activity_executor:
        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=[
                OccurrenceMaterializeWorkflow,
                AgentReconcileWorkflow,
                AgentHumanResumeWorkflow,
                AgentContinueWorkflow,
            ],
            activities=[
                activities.materialize,
                activities.reconcile,
                activities.human_resume,
                activities.continue_turn,
            ],
            activity_executor=activity_executor,
            max_concurrent_activities=activities.provider_concurrency,
        )
        await worker.run()
