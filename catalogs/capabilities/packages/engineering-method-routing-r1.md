# Engineering Method Supply Routing — R1

Date: 2026-10-16
Status: **CURRENT CENSUS / SELECTIVE ROUTING**

## Decision

Ordivon Engineer does not choose one framework as the engineering lifecycle. It keeps the existing FRAME -> PLAN -> EXECUTE -> VERIFY thin waist and selects the smallest useful external method set for each workload. Skills are procedural knowledge; Host/Runtime/repository-native owners retain durable state, execution and semantic authority.

## Canonical source families

| Source | Canonical count | Primary role | Default standing |
|---|---:|---|---|
| obra-superpowers | 14 | coding-agent discipline | Smallest applicable plan/TDD/debug/review/verify/branch discipline; not a mandatory universal lifecycle. |
| matt-native | 38 | issue/spec/repository engineering workflow | Use engineering skills when tracker/spec/ticket/domain-model/triage workflow is the natural work carrier; in-progress skills are experimental. |
| spec-kit-native | 10 | formal specification artifact pipeline | Use only when a formal spec/plan/tasks artifact chain has decision value; do not impose on small fixes or routine maintenance. |
| ecc-native | 311 | broad engineering/domain method library plus cross-harness workflow patterns | Search selectively. Use curated lifecycle/agentic skills as candidates; use language/framework/security/ops modules only when the target stack or risk triggers them; domain modules stay out of Engineer default routing. |
| project-ordivon-next | 30 | Ordivon-specific analysis methods and thin domain/collaboration routers | Invoke method-router only when method choice is materially uncertain; select the smallest specialist method set. Project domain routers do not become a universal engineering lifecycle. |
| rea-native | 1 | shipped-artifact/runtime reverse engineering | Use for binaries, packaged apps, firmware, managed/browser/runtime evidence. Do not use for ordinary source-repository architecture analysis. |
| ordivon-native-tools | 2 | native capability navigation and read-only model/provider capacity discovery | Use navigator for exact source selection; use CC Switch only for capacity/quota/provider availability, never as engineering method or credential authority. |

The full 406-entry classification is in engineering-method-routing-r1.json. ECC classification preserves its own install-modules.json membership first; Matt preserves its source folder family; the other smaller suites are classified explicitly.

## Practical categories

| Class | Meaning | Engineer use |
|---|---|---|
| LIFECYCLE_METHOD | frame/plan/implement/test/debug/review/verify/deliver procedure | primary method supply |
| MULTI_AGENT_COORDINATION | decomposition, subagents, worktrees, teams, handoff | compose with Host/Harness/Runtime; never replace them |
| SYSTEM_ANALYSIS_METHOD | decomposition, contracts, causal/reliability/control/info-flow/search methods | only when the dominant uncertainty calls for it |
| STACK_SPECIALIST | language/framework/database/ML/Apple engineering | activate only for the actual stack |
| SECURITY_ASSURANCE | AppSec/compliance/safety/security review | activate from risk/surface triggers |
| DEVOPS_OPERATIONS | deployment, infra, operations | activate from delivery/runtime needs |
| PERFORMANCE_OPTIMIZATION | benchmark/latency/throughput/parallel optimization | evidence-driven only |
| RESEARCH_DISCOVERY | external research/search/benchmarking | use when an engineering unknown requires research |
| KNOWLEDGE_GOVERNANCE | skill/docs/context/memory governance | support plane, not implementation authority |
| TOOL_PROVIDER_BRIDGE | specific external executable/provider bridge | on-demand; provider truth stays external |
| RESOURCE_ROUTING | model/provider quota/capacity selection | resource planning only |
| DOMAIN_SUPPORT | business/media/supply-chain/prediction/document/etc. workflows | outside default Engineer route; compose when workload requires |
| NON_ENGINEERING_SUPPORT / ENGINEERING_UTILITY | productivity or narrow setup utility | explicit use only |

## Default phase routing

### FRAME
- Light/ordinary acceptance framing: ecc-native/intent-driven-development.
- Tracker-backed spec: matt-native/to-spec.
- Formal spec chain: Spec Kit specify -> clarify/checklist.
- Brownfield mapping: ECC brownfield-retrospective; repository onboarding may also use codex-user/acquire-codebase-knowledge.

### PLAN
- Normal multi-step code work: obra-superpowers/writing-plans.
- Multi-PR / multi-session DAG: ecc-native/blueprint.
- Tracker ticket graph: matt-native/to-tickets / wayfinder.
- Formal Spec Kit workload: speckit-plan -> speckit-tasks.
- Only when analysis-method choice matters: project-ordivon-next/method-router.

### EXECUTE
- Independent planned tasks: obra-superpowers/subagent-driven-development plus Ordivon Harness/Runtime.
- Matt-owned spec/tickets: matt-native/implement-spec.
- Spec Kit-owned tasks.md: spec-kit-native/speckit-implement.
- Stack-specific implementation: select one ECC specialist skill, not the ECC catalog wholesale.
- Shipped/binary/runtime reverse engineering: REA only.

### VERIFY
- Universal completion discipline: obra-superpowers/verification-before-completion.
- Test-first implementation: prefer Superpowers TDD; Matt/ECC TDD are alternate specialized carriers.
- Hard bugs: obra-superpowers/systematic-debugging or matt-native/diagnosing-bugs.
- Standards + spec diff review: matt-native/code-review; Superpowers review skills handle request/feedback discipline.
- Broad build/type/lint/test/security/diff gate: ecc-native/verification-loop.
- Spec Kit analyze/converge verifies its artifact chain, not real-world semantic completion.
- `spec-kit-native/speckit-taskstoissues` is currently marked Deprecated upstream; retain only for explicit compatibility, never default routing.

### DELIVER / OPERATE
- Branch integration decision: obra-superpowers/finishing-a-development-branch.
- PR body: matt-native/pr.
- Commit/workflow mechanics: ECC git-workflow / conventional-commit-review.
- Provider capacity: CC Switch is resource routing only.

## Overlap decisions

1. TDD is not triplicated at runtime. Superpowers is the normal discipline; Matt TDD is preferred inside a Matt tracker/spec workflow; ECC TDD is used when an ECC orchestration/stack workflow already owns the local procedure.
2. Planning is size- and carrier-dependent. Superpowers for ordinary implementation plans, ECC Blueprint for large DAGs, Matt for tracker graphs, Spec Kit for formal spec artifacts.
3. Verification layers are not substitutes. verification-before-completion is the minimum claim discipline; ECC verification-loop is a broad engineering gate; Spec Kit analyze/converge only checks Spec Kit artifacts.
4. Multi-agent methods do not own durability. ECC/Superpowers describe decomposition and isolation; Ordivon Host owns durable collaboration state and Runtime owns Workspace/Job/Attempt truth.
5. Ordivon analysis methods never become mandatory ceremony. method-router selects the smallest method set only when the reasoning method can change a decision.
6. REA and CC Switch are executable/specialist bridges, not engineering lifecycles.

## Invocation/currentness note

The installed canonical Native Six census is 14 Superpowers, 38 Matt, 311 ECC, 10 Spec Kit, 1 REA and 2 native-tool Skills. skills.list in implicit mode intentionally exposes a smaller safe/model-visible subset; exact source-qualified IDs can still resolve in explicit mode (for example obra-superpowers/systematic-debugging, matt-native/implement-spec, and spec-kit-native/speckit-plan). Therefore implicit catalog size must not be mistaken for installation drift. The `standing` field in the JSON is routing guidance only; Skills MCP remains authoritative for trust, eligibility, invocation mode and exact current binding.

## Verification

- Source roots and exact counts were checked against the Ordivon native-six regression.
- ECC: all 311 skills are covered by ECC-owned install-module categories; zero unmapped.
- This classification does not grant tool, credential, provider, merge, publication, or domain authority.
