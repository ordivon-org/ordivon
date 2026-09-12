# Local Capability Pack R1

Date: 2026-09-13

This is an auditable local environment snapshot, not a Registry, ontology, subsystem list, or required Ordivon topology. Skills and tools are consumed directly from mature external ecosystems and loaded only when a real task needs them.

## Agent / harness

- Codex: installed at `/root/tools/bin/codex`.
- Agent Skills: user scope under `~/.codex/skills`; project-local skills remain allowed where project-specific knowledge is genuinely needed.
- Skill installation/update mechanism: GitHub CLI `gh skill` (GitHub CLI 2.97.0 observed), with commit pinning for external skills.

## Selected user-level skills

### General engineering

- `acquire-codebase-knowledge`
  - source: `github/awesome-copilot`
  - pinned commit: `7568a482ce2df38f8965ab5336a3220db796a4ba`
  - purpose: repository-scale onboarding/mapping only; not routine edits.
  - compatibility note: uses GitHub/Copilot `argument-hint` frontmatter extension; accepted by the current `gh skill`/Codex path but rejected by strict `skills-ref` Agent Skills Core validation.
- `security-review`
  - source: `github/awesome-copilot`
  - pinned commit: `7568a482ce2df38f8965ab5336a3220db796a4ba`
  - purpose: code-focused vulnerability review.
- existing Codex skills retained: `playwright`, `security-best-practices`, `security-threat-model`.

### Research and scientific work

- `literature-review`
  - source: `msimchowitz/writing-skills`
  - pinned commit: `214981fe02326f27b0fc8790d00eb4b731607073`
  - purpose: evidence-led review contract, source ledger, claim/evidence matrix and review audit.
  - selected instead of the heavier K-Dense literature-review skill because the latter included optional external LLM/API and installer paths not needed in the minimal local pack.
- `experimental-design`
- `statistical-analysis`
- `scientific-writing`
- `scientific-visualization`
- `peer-review`
  - source for these five: `K-Dense-AI/scientific-agent-skills`
  - pinned commit: `c1ed16d97dd61ff50a3bd46dd353e4a55fd77f34`

### Artifact work

- `artifact-work`
  - source: local `/root/projects/ordivon-next/.agents/skills/artifact-work`
  - source knowledge authority: `/root/projects/ordivon-artifact-v2@39b6281b9b59c5d9d372a04e36f845758a7c93cf`
  - purpose: standards-first creation/verification routing for presentations, images, datasets, audio/video, geospatial, 3D and software-release artifacts.

## Existing executable capability base

Observed locally and therefore not reinstalled for this pack:

- automation/integration: n8n;
- containers: Docker, Podman;
- infrastructure/configuration: OpenTofu, Ansible;
- languages/tooling: Python, Node/npm/pnpm, uv/uvx, Git, ripgrep, jq, yq;
- document/visual/media: Quarto 1.10.18 (bundled Pandoc 3.10), Typst, FFmpeg, ImageMagick, Blender, Godot, qpdf;
- software supply chain/security: Syft, Trivy, Skopeo, Cosign;
- data/geospatial: DuckDB, SQLite, GDAL/OGR.

Other capabilities continue to live in their source projects/services, including Runtime, Temporal-facing Operations, Network, Security, Artifact and Distribution providers. They are not copied into this pack.

## Selection policy

Do not install a large skill collection by default. Add a skill only when all of the following are true:

1. a real workload needs the capability now;
2. the current harness/model does not already handle it adequately;
3. a mature external skill exists and is preferable to local invention;
4. the skill is reviewed before first execution, especially scripts/network/credential behavior;
5. source/version is pinned when reproducibility or trust matters.

Prefer official or high-quality maintained sources. Remove or replace skills whose scope overlaps without measurable benefit.

## Security / supply-chain note

`gh skill` warns that third-party skills are not GitHub-verified execution authority. Installation is not trust promotion. External skills in this pack are pinned and were screened for obvious high-risk command/network/credential patterns before routine use. Script execution still requires task-local judgment and the normal execution/authority boundary.

## Operational rule

The pack is considered sufficient until a real project demonstrates a missing capability. Future work should default to producing outcomes rather than expanding the pack.

When a gap appears:

`real task -> search mature skill/tool -> review -> pin/install -> use -> verify outcome`

Only build local capability when no mature option is sufficient and the gap repeats.
