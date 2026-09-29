---
name: research-capability-routing
description: "Route an already-scoped Research action to the thinnest specialized Skill, provider, workflow engine, data-plane binding, Runtime, or publication owner. Use after Study/method scope is known when choosing who should perform literature discovery, citation resolution, EDA/statistics, document parsing, data transforms, scientific DAGs, durable processes, physical execution, provenance, or publication mechanics. Does not create Studies, choose scientific methods, authorize effects, or decide scientific completion."
compatibility: "Uses explicit problem classes plus natural-owner currentness observations. Study Birth and Research-v2 remain separate owners; Skills are advisory; provider/tool availability is not inferred from documentation."
metadata:
  source-authority: "Ordivon Research capability index + routing profile + live natural-owner observations"
---

# Research Capability Routing

Use this Skill when the research question/method is already scoped and the remaining question is **which specialized capability should do the next action, through which owner-native surface, and what must verify it**.

## Hard boundary

This Skill owns no scientific truth and performs no provider effect. It compiles a route only.

Do not use it to replace:

- `research-study-birth` for creating/adopting a Study or resolving current Research-v2 defaults;
- `method-router` when the unresolved question is which reasoning/scientific analysis method to apply;
- Study/domain standards for scientific semantics;
- Runtime for Job/Attempt truth;
- Temporal for durable process state;
- Snakemake for scientific file/artifact DAG semantics;
- Artifact/publication Skills for their own carrier gates;
- Human/submission authority.

## Definition and provider bindings

Stable Research capability meaning is defined once in:

```text
profiles/research/capability-index/research-capability-index-r1.json
```

Specialist/provider routing is defined in:

```text
references/research-capability-routing-r1.json
```

The Gateway release projection is mechanically generated from those sources. Do not hand-edit `services/gateway/src/ordivon_gateway/research_routes.py` as a second policy source.

## Operating procedure

1. If the public Gateway currently exposes `capability.search`, use it for bounded Research capability discovery; otherwise use the canonical index directly rather than guessing from memory.
2. Translate the already-scoped next action into one exact `problemClass` from `references/research-capability-routing-r1.json`. Do not pass free-form goals to the deterministic resolver.
3. Obtain currentness from the natural owner before selecting a provider route:
   - Skill procedure: `skills.resolve` / `skills.read`; preserve dependency and scan/trust state.
   - Study data plane: current Research-v2 `ordivon-research-study defaults`; do not copy remembered defaults.
   - Runtime: `runtime.describe` / Gateway projection as appropriate.
   - Temporal/provider/toolchain: provider-native health/version/binding surface.
   - caller-bound connector: current application/plugin connection state.
4. Represent those observations as an authority-keyed object and run the deterministic resolver.
5. If the public Gateway currently exposes `capability.resolve`, it may be used to bind an exact current Skill or canonical invocation recipe for the selected stable `research.*` capability. Resolution remains metadata, not authorization or execution.
6. Execute only through the returned owner-native invocation surface. A route decision never grants authority.
7. Verify using the returned verification boundary plus the Study/domain acceptance contract.
8. If the resolver returns HOLD, repair/activate the missing natural owner or change the explicit requirement. Do **not** silently fall back to a generic Agent.

## Resolver

List known problem classes/routes:

```bash
python .agents/skills/research-capability-routing/scripts/route.py list
```

Plan from explicit currentness observations:

```bash
python .agents/skills/research-capability-routing/scripts/route.py plan \
  --problem-class scholarly.discovery \
  --observations /tmp/research-route-observations.json
```

Example observation shape:

```json
{
  "skill:paper-lookup": {
    "state": "available",
    "bindingRef": "codex-user/paper-lookup"
  }
}
```

For Research-v2 data-plane routes, bind the live `defaults` result into `study-data-plane.bindings`; examples include `data.analytical-query`, `data.dataframe-transform`, `data.normalization`, `data.analytical-storage`, `data.validation`, and `workflow.scientific-dag`. The current Study owner decides provider values.

## Three graph rule

Never collapse these because all three look like workflows/graphs:

- `workflow.scientific-dag` → Snakemake / Study-owned scientific DAG;
- `workflow.durable-process` → Temporal durable workflow history;
- `execution.physical` → Runtime Workspace/Job/Attempt physical execution.

The route can compose them, but none substitutes for the other.

## Source verification

```bash
mise run research-routing:verify
```

This validates both machine-readable source contracts and proves the Gateway Research projection is current with them. `mise run gateway:verify` independently qualifies Gateway behavior.

## Stop condition

Stop routing when one exact currently-ready route is selected, or when a typed HOLD identifies the missing currentness/capability. Continue through the selected owner; do not let this Skill absorb execution or domain completion.
