# Harness Agent Instructions

Scope: `services/harness/`. Inherit repository-root `AGENTS.md`; this file is navigation, not a second authority, policy engine, or Skill registry.

## Owner and source cut

- Harness owns one bounded Agent Run, its cognition/control transitions, Provider/Tool continuity, evidence, and completion proposal.
- Host/domain owns Task and final semantic acceptance; Runtime owns Workspace/Job/Attempt/physical effects; Gateway/Provider owns transport and external delivery. Do not treat a Run or Job as domain completion.
- Establish exact Git source revision and current consumer before editing. Linux and Windows Runtime Workspaces may be on different commits; a detached Workspace is not proof of release or deployment.
- Read `README.md`, `ARCHITECTURE.md`, `docs/STATUS.md`, and `docs/authority.md` selectively. Prefer current source and exact runtime receipts over conflicting historical prose.

## Find the actual capability

| Need | Current implementation | Verification / guidance |
| --- | --- | --- |
| Run creation/resume | `src/ordivon_harness/agent_run.py`, `standalone.py`, `core_contracts.py` | `tests/test_p0_standalone_runner.py`, `docs/QUICKSTART.md` |
| Model-turn policy | `ordivon/loop.py`, `ordivon/run_deadline_selection.py`, `ordivon/provider_retry_policy.py`, `turn_projection.py`, `control.py` | `tests/test_loop_decision_operators.py`, `tests/test_loop_decision_consumer.py` (actual Run), `tests/test_r1_single_capability_truth.py` |
| Durable cognition | `working_view.py`, `ordivon/cognition_admission.py`, `ordivon/working_set_queries.py` | `docs/STATUS.md` |
| Tool calls and programs | `ordivon/tool_bridge.py`, `tool_program_contract.py`, `tool_program_resolution.py`, `tool_program.py` | `formal/ToolProgramSafetyR1.tla`, `tests/test_tool_program_model_refinement.py`, `tests/test_p2_tool_program.py` |
| Physical effects | `runtime_port.py`, `execution_binding.py`, `gateway_execution_port.py` | `tests/test_p0_execution_binding.py` |
| Durable Run storage | `postgres_store.py`, `store.py`, `store_ops.py` | `tests/test_postgres_harness_store.py`, `docs/OPERATIONS.md` |
| Tool/Provider recovery | `ordivon/provider_lifecycle.py`, `ordivon/run_recovery.py`, `tool_program_recovery.py` | `tests/test_p2_tool_program_recovery.py` |
| Structured terminal result | `completion.py`, `structured_result_conformance.py` | `tests/test_structured_result_conformance.py` |
| Browser / human handoff | `scripts/browserless_*.py`, `scripts/cft_human_*.py`, `systemd/` | `docs/OPERATIONS.md`; check actually loaded service config |
| Research & evidence | `research/authority/CURRENT.json`, `formal/`, `evals/`, `evidence/index.json` | `docs/VERIFICATION.md` |

## Agent execution rules

1. Discover from the natural owner/tool substrate; only an **exact turn-admitted** Tool may be called. An installed plugin, a Skill, or a catalog entry is not an effect grant.
2. Keep canonical history separate from Agent-selected WorkingSet; source presence is not cognition or source truth.
3. Commit Tool intent before dispatch, bind a stable physical request identity, and reconcile UNKNOWN with the effect owner before redispatching.
4. Budget every physical ToolProgram step; observation references consume already observed, exact structured content, never arbitrary expressions.
5. Treat Provider/Runtime liveness, release installation, Domain acceptance, and repository HEAD as different facts.
6. For first-party CLI use `HARNESS_PG_DSN` / optional `HARNESS_PG_SCHEMA`; do not auto-fallback to SQLite. **Legacy direct Python APIs still require consumer audit before deletion.**
7. Use `mise tasks ls`, the scoped `mise run formal:tool-program` TLC model, affected Python refinement/consumer tests, relevant fault/replay/PG integration checks, and installed read-back. Do not treat model CHECK as implementation refinement, or a skipped test as PASS. The new model check is a candidate task until real TLC execution qualifies it for the release gate.
8. Avoid a new LEGO registry, provider router, governance framework or generic memory ontology. Choose DELETE → REUSE → COMPOSE → CREATE based on a real consumer and the existing owner contract.
9. For user action and step-by-step capability guidance see `docs/CAPABILITY_GUIDE.md`. For unusual formal method work use root `.agents/skills/recursive-lego-calculus/SKILL.md`.

## Cleanup

Use `git status`, `git grep`, package import search and deployed consumer checks before renaming or retiring a tracked path. Remove generated cache only under the owned project root; never sweep `/var/lib`, `C:\\Windows`, PG schemas, user browser profiles, other agents' Workspaces or release artifacts as a by-product. Old SQLite code is removable only after direct Python/API and service consumers are retired, not because first-party CLI is PG-only.
