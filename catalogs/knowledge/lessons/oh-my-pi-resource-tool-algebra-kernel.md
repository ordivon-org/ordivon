# Oh My Pi Resource + Tool Algebra Kernel — extracted interface design lessons

Status: **REGISTERED / PROTOTYPE-READY DESIGN RULE**  
Registered: 2026-09-14

## One-sentence model

**A large capability ecosystem should expose a small set of orthogonal model-facing operations and typed resource references, keeping backend diversity behind adapters rather than making the model memorize hundreds of provider-specific Tool names.**

## Problem

As an Agent gains browsers, repositories, child Agents, Artifacts, MCP servers, files, history and external data, a naive Tool surface grows without bound:

```text
read_file
read_agent_output
read_history
read_github_issue
read_pdf
read_artifact
...
```

Large flat Tool catalogs increase selection ambiguity and schema/context cost.

OMP repeatedly uses compact action families (`lsp`, `debug`, `task`, `hub`) and internal resource schemes (`agent://`, `history://`, artifact/resource routing) rather than exposing every backend operation as a new conceptual primitive.

## Design law

**Compress interface vocabulary, not authority or evidence.**

One model-facing operation may route to many backends, but the resolved provider/resource identity must remain explicit in execution/evidence.

## Two primitives

### 1. Action families

Use one semantic Tool with an `action` discriminator when operations share lifecycle, authority and result semantics.

Good candidates:

```text
lsp(action=definition|references|rename|...)
debug(action=launch|stack_trace|variables|...)
hub(action=list|message|cancel|wait|...)
```

Bad collapse:

```text
world(action=pay_invoice|delete_repo|send_email|trade|...)
```

These do not share consequence semantics or authority merely because one mega-Tool is convenient.

### 2. Typed resource references

Represent large or deferred content by URI-like handles:

```text
agent://<childRunId>
history://<childRunId>
artifact://<artifactId>
workspace://<workspaceId>/<path>
```

The exact schemes are replaceable. Required properties are:

- typed resolver;
- stable identity/reference;
- bounded default projection;
- explicit full/partial read;
- provenance preserved;
- no implicit authority escalation from possessing a URI string.

## Minimum resolver API

```ts
type ResourceRef = string;

type ResourceReadRequest = {
  ref: ResourceRef;
  offset?: number;
  limit?: number;
  selector?: string;
};

type ResourceReadResult = {
  ref: ResourceRef;
  contentType: string;
  content?: string;
  artifactRef?: string;
  complete: boolean;
  nextOffset?: number;
  provenance: object;
};
```

Resolvers register by scheme:

```ts
registerResolver("agent", childOutputResolver)
registerResolver("artifact", runtimeArtifactResolver)
registerResolver("workspace", runtimeWorkspaceResolver)
```

## Resource references vs data copies

Prefer references when:

- output is large;
- multiple consumers may inspect different slices;
- content already has an authoritative store;
- injecting full content would waste model context.

Do not use references to hide small decision-critical data the model needs immediately.

## Tool discovery interaction

Resource resolvers and Tool providers are separate concepts:

- Tool = action capability;
- Resource = addressable observation/content.

An MCP provider may expose both, but Harness should not force them into one namespace.

## Result shaping

Every Tool should distinguish:

```text
model-visible summary/content
structured details
full Artifact/resource reference
```

Example child result:

```text
content: "Child A found two likely causes..."
details: {status, usage, schemaValidated:true}
resource: agent://childA
```

This reduces context while preserving inspectability.

## When to create a Tool family

Combine operations only if most are true:

1. same provider/lifecycle owner;
2. same approval/consequence class or safely action-classifiable;
3. shared state/session;
4. similar result envelope;
5. model benefits from learning one conceptual object;
6. action enum remains bounded and coherent.

Otherwise keep separate Tools.

## Prototype

Build a small Harness-side registry:

```ts
ToolRegistry
ResourceResolverRegistry
```

Register:

- `lsp` action family;
- `hub` action family;
- `workspace://` reader;
- `artifact://` reader;
- `agent://` child output reader.

Then compare model-facing Tool catalog size and task success against a deliberately flattened equivalent Tool set.

## Acceptance tests

1. One `lsp` schema routes multiple actions without losing action-specific validation.
2. Resource read returns bounded slices with continuation.
3. `agent://` resolves child output without copying it into parent transcript at spawn completion.
4. Resolver preserves authoritative underlying id/provenance.
5. Possessing a resource ref does not grant a Tool action not admitted to the Run.
6. Unknown scheme/action fails explicitly.
7. Large content stays out of model context unless requested.
8. Flattened-vs-algebra benchmark measures Tool-selection errors and schema token cost.

## Project-study acceptance

### One-sentence test

PASS: OMP demonstrates that model-facing Tool ergonomics benefit from compact semantic action families and deferred typed resources.

### Prototype test

PASS: the registry/resolver split and combination criteria are sufficient to prototype a smaller Tool algebra without weakening Ordivon authority boundaries.

## Verdict

**PASS — CROSS-CUTTING HARNESS INTERFACE RULE; USE TO CONTROL CAPABILITY-SURFACE EXPLOSION.**
