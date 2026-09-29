# Provider: ComfyUI

Status: **PROTOTYPE-READY / ON-DEMAND GENERATIVE-MEDIA PROVIDER / NOT LOCALLY INSTALLED**
Role: graph-based generative media workflow engine for image, video, audio, 3D, text and related model pipelines.

## One-sentence understanding

**ComfyUI turns generative-media processing into a serializable typed node graph whose dependencies, model operations, caching, queueing and outputs are executed by a dedicated inference engine rather than reimplemented by the calling Agent.**

## Current local observation — 2026-09-14

No `comfyui`/`comfy` executable or obvious local ComfyUI installation was observed in the current workstation paths checked during this study.

Do not install it merely because the project passed architectural study. Activate/install when a real image/video/audio/3D generation workload justifies model storage, GPU/VRAM use and node-pack maintenance.

## When Ordivon should route work here

Prefer ComfyUI when the task requires a repeatable generative-media pipeline such as:

- text/image-to-image generation;
- inpainting/outpainting;
- ControlNet/reference-conditioning workflows;
- multi-stage upscaling/restoration;
- image editing/model chaining;
- video generation/interpolation/post-processing;
- audio generation;
- 3D/vision model pipelines;
- repeated variation generation where seeds/models/parameters/workflow should remain inspectable;
- production pipelines that benefit from a reusable workflow graph rather than one opaque model call.

Prefer thinner providers when appropriate:

- one simple hosted-model call with no multi-stage composition -> direct API/provider;
- deterministic image/video processing -> ImageMagick/FFmpeg/OpenCV/etc.;
- manual high-fidelity editing/modeling -> Photoshop/Krita/Blender or other native tools;
- game/runtime rendering -> Godot/Unity/etc.;
- final artifact packaging/technical validation -> Artifact provider.

## Core primitives

### Typed node

A node declares an operation with typed inputs/outputs and an implementation function.

Classic custom-node shape includes concepts such as:

- `INPUT_TYPES`;
- `RETURN_TYPES`;
- `FUNCTION`;
- `CATEGORY`;
- registration through `NODE_CLASS_MAPPINGS`.

The node owns one operation; the graph owns composition.

### Workflow graph

A workflow is a directed graph of node instances and links. The UI representation is serializable as versioned Workflow JSON. A separate API-format graph is used for execution through the server/cloud API.

Do not conflate:

- **UI Workflow JSON** — editor/layout/subgraph/workflow artifact;
- **API-format workflow/prompt** — executable graph submitted to the engine.

The workflow graph is the reusable procedural artifact. The UI canvas is only one authoring surface.

### Dependency-driven execution

Execution starts from requested output nodes and resolves upstream dependencies. ComfyUI's executor maintains a topological execution list rather than executing nodes according to canvas position.

Conceptually:

```text
requested outputs
      ↓
required ancestors
      ↓
topological ready set
      ↓
execute node
      ↓
cache output
      ↓
unblock dependents
```

### Incremental execution / cache

Node results are cacheable by input signature and change state. If upstream inputs and relevant node state have not changed, cached outputs can be reused and unaffected branches need not re-run.

This is one of ComfyUI's most important advantages for expensive media inference: changing one prompt/parameter should not imply recomputing unrelated graph regions.

The current engine supports multiple cache policies including classic hierarchical cache, LRU, RAM-pressure-aware cache and no-cache modes.

### Model/resource management

ComfyUI owns model loading/offloading, VRAM/RAM strategy and inference-specific resource handling. The caller should not recreate a parallel Ordivon model-memory scheduler.

Models/checkpoints, VAEs, text encoders, LoRAs, ControlNets, adapters, upscalers and other model assets remain provider-owned execution dependencies.

### Queue / job

Local ComfyUI exposes a queue-oriented server API. A workflow submission receives a prompt/job identifier, progress can be observed through WebSocket/polling, history can be inspected and outputs retrieved.

Newer Comfy API v2 extends this toward durable/pollable jobs and explicit assets, but ComfyUI job success remains provider execution state rather than Ordivon domain completion.

### Workflow / output provenance

Workflows can be saved as JSON. Supported generated media can embed workflow/prompt metadata so a generated output can recreate the workflow/seed context later.

This is useful provenance for generative production, but it is not sufficient rights/authenticity provenance by itself. C2PA or other media-provenance requirements remain separate when needed.

### Subgraph

Subgraphs package a group of nodes behind a smaller typed interface and can be nested/reused.

This is the correct abstraction for hiding low-level pipeline complexity without inventing a second Ordivon workflow language.

### App Mode

App Mode exposes selected workflow inputs/outputs through a simplified interface while keeping the underlying graph hidden from the end user.

This provides a path from expert workflow construction to reusable product-like capability:

`expert graph -> exposed parameters -> simple application surface`

### Custom nodes / Registry

Custom nodes are executable Python/JS extensions. The Comfy Registry adds globally unique packages, semantic versioning, immutable published versions, deprecation and security scanning/verification.

Workflow reproducibility depends not only on workflow JSON but also on exact node-pack versions, model assets and runtime environment.

## Ordivon boundary

ComfyUI owns:

- generative-media node definitions;
- graph dependency execution;
- inference cache;
- model loading/offloading and VRAM/RAM mechanics;
- execution queue/history;
- custom-node ecosystem;
- workflow editor/UI/App Mode;
- provider-specific inference output files.

Ordivon owns:

- deciding that a generative workflow is the right capability;
- selecting/parameterizing an appropriate proven workflow;
- composing Media/Research/Artifact/Distribution around it;
- target-level acceptance criteria;
- verification that the generated artifact is usable, lawful, technically valid and fit for the requested outcome.

Do not create `Ordivon Media DAG`, custom node runtime, model manager or inference cache merely to wrap ComfyUI.

## Boundary with n8n

Both use node graphs, but the nodes represent different realities.

### n8n

`event/API/business integration graph`

Best for webhooks, SaaS operations, deterministic data routing and external service automation.

### ComfyUI

`tensor/media/model-compute graph`

Best for inference pipelines, image/video/audio/3D transformations and expensive model composition.

Ordivon may invoke a ComfyUI workflow from n8n when a business/integration workflow needs a media-generation step; neither should replace the other.

## Boundary with Artifact / Media

ComfyUI is an execution provider inside Media, not the owner of final deliverable correctness.

Example:

```text
source/brief
   ↓
Media design
   ↓
ComfyUI workflow
   ↓
generated media
   ↓
Artifact/native technical validation
   ↓
rights/accessibility/QC
   ↓
Distribution if authorized
```

A successful workflow run does not prove visual quality, factual correctness, accessibility, rights clearance, platform acceptance or audience effectiveness.

## Security / supply-chain boundary

Custom nodes are executable code and may execute Python/JS with process authority. Treat node packs like dependencies/plugins, not harmless workflow data.

Prefer:

- official/built-in nodes when sufficient;
- Registry-published/versioned nodes;
- reviewed and pinned custom-node versions for reproducible workflows;
- separate environments for untrusted/experimental node packs;
- no arbitrary `git clone`/pip-install-from-workflow behavior;
- model hashes/licenses recorded when outputs matter operationally.

The Registry explicitly prohibits or flags dangerous patterns such as `eval`/`exec`, runtime pip installation and obfuscated code, but registry checks are not a substitute for host isolation and review.

## Reproducibility model

A workflow JSON alone is not a complete reproducibility package.

A practical reproducibility identity should include at least:

```text
workflow graph/version
+ API/UI conversion if applicable
+ node-pack names + versions
+ model/checkpoint/LoRA/etc. identities/hashes
+ relevant seeds
+ input assets
+ key runtime/model settings
+ ComfyUI/runtime version
```

Generated outputs with embedded workflow metadata are useful starting evidence, not a complete environment lock.

## Prototype recipe

A minimal ComfyUI-like engine needs only:

1. define a typed node interface;
2. register a few node classes;
3. represent node instances/links as JSON;
4. validate referenced node classes and input types;
5. identify requested output nodes;
6. traverse dependencies/topologically schedule ready nodes;
7. execute each node and store outputs by node/socket;
8. compute an input signature and reuse cached results when unchanged;
9. expose `submit -> job id -> progress/history -> outputs`;
10. serialize/load the workflow graph.

Example proof graph:

```text
LoadInput
   ↓
TransformA
   ↓
TransformB
   ↓
SaveOutput
```

Add one branch and input-signature cache to demonstrate partial re-execution. No diffusion model is required to prove the architecture.

## Prototype readiness gate

**PASS.** Typed nodes, graph serialization, dependency execution, cache semantics, custom-node registration, job/API surface and workflow provenance are understood well enough to implement a minimal functional graph executor or consume ComfyUI directly.
