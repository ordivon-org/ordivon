# n8n + DeepSeek Harness — Node Composition Lessons R1

Status: DESIGN INPUT
Checked: 2026-09-17
Purpose: refine `project-kernel-decomposition` from module documentation into recursively composable architectural nodes.

## One-sentence synthesis

**n8n shows how to make behavior composable as explicit nodes and connections; DeepSeek Harness shows how to make architecture composable as replaceable plugin/service seams; Ordivon should combine both so every decomposed project ends as a typed graph of independently testable architectural LEGO blocks.**

## n8n: the useful idea

n8n defines a workflow as nodes connected together. Nodes can trigger work, fetch/send data, process data, and express flow control. Custom/community nodes extend the graph without changing the workflow model. Node-level execution behavior also exposes retry and error handling.

Architectural lesson:

```text
complex behavior
  -> explicit node
  -> explicit inputs/outputs
  -> explicit connection
  -> local configuration
  -> local failure behavior
  -> graph composition
```

What to retain:

- explicit `nodes + connections` graph;
- typed trigger/action roles;
- extensibility through custom nodes;
- node-local retry/error policy;
- inspectable execution graph;
- reusable subgraphs/templates.

What not to copy literally:

- treating every architectural responsibility as a sequential action;
- UI coordinates as architecture;
- one generic data envelope as sufficient for authority/security/effect boundaries;
- workflow graph as the system's durable truth model.

## DeepSeek Harness: the useful idea

DeepSeek Harness is built around Cordis plugins. Services such as tools, LLM, agents, and workflow engine are capabilities exposed on context; consumers declare injected dependencies and wait until those services are ready. The workflow engine is an optional seam outside the agent loop, and the model-facing workflow tool is kept separate from the underlying engine implementation.

Architectural lesson:

```text
consumer
  -> stable service contract
  -> provider implementation
  -> replace provider without changing consumer surface
```

The architecture documentation also emphasizes that there is no privileged core to patch: product pieces are plugins contributing services, events, and reversible effects.

What to retain:

- service seam as first-class architectural unit;
- explicit dependency injection;
- provider/consumer separation;
- replaceability by configuration;
- optional capability kept outside core;
- event surfaces separate from control ownership;
- model-facing schema separate from execution engine.

What not to copy literally:

- one shared `ctx` object as Ordivon's universal ontology;
- in-process plugin lifetime as a substitute for durable Service/Runtime state;
- worker-thread VM as a security boundary;
- Harness session/event semantics as cluster-wide Agent Service truth.

## Combined Ordivon model

```text
                    PROJECT
                       |
                responsibility map
                       |
                       v
               ARCHITECTURE GRAPH

  +-------------+    typed edge    +-------------+
  | Atomic Node | ----------------> | Atomic Node |
  +-------------+                   +-------------+
       |                                  |
   stable ports                       stable ports
       |                                  |
 provider may swap                  provider may swap
```

Each node carries more information than an n8n action:

```text
responsibility
kind
authority
state/effect ownership
input/output ports
failure semantics
replaceability
acceptance test
```

## Crucial distinction: architecture graph != execution graph

An execution graph answers:

> What runs next?

An architecture graph answers:

> Which responsibility owns this fact/effect/decision, and through what contract may another block interact with it?

Some architecture nodes later compile into executable workflow nodes. Others are stores, registries, policy seams, identity authorities, gateways, observers, or projections.

## Recursive decomposition algorithm

```text
project
  -> identify product shell / kernel / substrates
  -> split kernel into responsibility nodes
  -> run Atomicity Gate on every node
      -> PASS: freeze as leaf LEGO block
      -> FAIL: split into child nodes
  -> type every edge
  -> define ports/contracts
  -> define acceptance per leaf
  -> derive minimal connected subgraph
  -> implement clean-room vertical slice
```

The recursion stops at architectural atoms, not source-file atoms.

## Implication for Ordivon

This method can become the common representation for future studies of Runtime, Host, Harness, Skill MCP, Agent Plugin, Agent Service, external frameworks, and research tooling. Different upstream products can then be compared as graphs of equivalent responsibilities rather than by package names.

That enables a stronger comparison primitive:

```text
AWS.Registry.Node
Google.Registry.Node
Foundry.Registry.Node
Ordivon.Registry.Node
```

instead of comparing entire products wholesale.
