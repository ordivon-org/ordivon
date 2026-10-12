---
name: research-capability-routing
description: "Route an already-scoped Research action to the thinnest specialized Skill, provider, workflow engine, data-plane binding, Runtime, or publication owner. Use after Study/method scope is known when choosing who should perform literature discovery, citation resolution, EDA/statistics, document parsing, data transforms, scientific DAGs, durable processes, physical execution, provenance, or publication mechanics. Does not create Studies, choose scientific methods, authorize effects, or decide scientific completion."
compatibility: "Uses explicit problem classes plus current owner-native system observations, not approval from a fixed agent identity. Study Birth and Research-v2 retain their own truth boundaries; Skills are advisory."
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

Research capability meaning and specialist routing stay at these canonical Research/Skill sources. Gateway does **not** carry a generated `research.*` semantic projection or a Research-specific resolver; generic Gateway `capability.search` / `capability.describe` remain owner-routing surfaces only.

## Operating procedure

1. Use the canonical Research capability index for Research capability discovery. Generic Gateway `capability.search` may be used only for its current owner/execution projection when that is relevant; it is not the Research taxonomy.
2. Translate the already-scoped next action into one exact `problemClass` from `references/research-capability-routing-r1.json`. Do not pass free-form goals to the deterministic resolver.
3. Freeze the intended canonical Skill identity from the selected profile route `invocation.canonicalSkillId` **before** resolving availability. A current but different Skill is not the intended Skill and must fail closed. Active Agents may take the relevant capability role; do not wait for a named previous Agent to approve discovery.
4. Obtain currentness from the corresponding owner-native system (provider, Skills, Study, Runtime), not a fixed Agent persona:
   - Skill procedure: use the route profile only to identify the intended canonical Skill. The offline resolver can detect missing identity/generation fields or a canonical mismatch, but it **cannot authenticate caller-carried generation hashes**. Even a complete canonical Skill observation therefore returns `HOLD_OWNER_VERIFICATION_REQUIRED`; establish currentness only through a direct `skills.resolve` followed by exact fenced `skills.read`. Do not feed SHA-shaped caller strings back into the router as proof of currentness.
   - Study data plane: current Research-v2 `ordivon-research-study defaults`; do not copy remembered defaults.
   - Runtime: `runtime.describe` / Gateway projection as appropriate.
   - Temporal/provider/toolchain: provider-native health/version/binding surface.
   - caller-bound connector: current application/plugin connection state.
5. Represent non-Skill provider observations as an authority-keyed object and run the deterministic resolver. Skill observations may be supplied for mismatch/missing-evidence diagnostics, but they never upgrade offline routing into owner-currentness truth.
6. For a Skill candidate in `HOLD_OWNER_VERIFICATION_REQUIRED`, take its `canonicalSkillId` / invocation coordinates and resolve that Skill directly through the Skills owner (`skills.resolve` / fenced `skills.read`). Do not rerun the offline router to manufacture a second currentness verdict.
7. Execute only through the owner-native invocation surface after that direct owner verification. A route decision never grants authority.
8. Verify using the returned verification boundary plus the Study/domain acceptance contract.
9. If the resolver returns HOLD, identify missing provider-native evidence, wrong canonical identity, or missing actual capability. An active qualified Agent may take the corresponding work role to repair it; do **not** silently route to a generic Agent or claim that a fixed owner persona must respond.

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
    "bindingRef": "codex-user/paper-lookup",
    "skillId": "codex-user/paper-lookup",
    "snapshotRevision": "sha256:<owner-snapshot>",
    "instructionDigest": "sha256:<owner-instruction>",
    "packageRevision": "sha256:<owner-package>",
    "readDigest": "sha256:<fenced-skill-read>"
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

This validates the canonical machine-readable Research capability index, routing profile, deterministic routing behavior, and typed HOLD semantics. Gateway has no Research semantic projection to keep current; `mise run gateway:verify` independently qualifies the remaining generic Gateway behavior.

## Stop condition

Stop routing when one exact non-Skill route is currently ready, or when a typed HOLD identifies the next owner action. For Skill routes, `HOLD_OWNER_VERIFICATION_REQUIRED` is the successful routing boundary: use the emitted canonical Skill coordinates for direct Skills-owner resolve/read, then continue through that owner-native executable interface. Do not transfer execution, currentness, or domain-completion authority into this Skill.
