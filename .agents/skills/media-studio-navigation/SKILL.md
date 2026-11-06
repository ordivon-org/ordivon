---
name: media-studio-navigation
description: "Find the appropriate existing Ordivon Media capability and an explicitly selected Studio Production for a human-facing creative work. Read source-owned Claims, production context, equipment options and current evidence without inventing a new production registry or transferring source authority."
compatibility: "Ordivon monorepo capabilities/media source; Python 3 for dependency-light discovery."
metadata:
  source-authority: "capabilities/media/AGENTS.md and ordivon_studio.agent_surface schemas"
---

# Media Studio Navigation

Use this source-owned procedure when the caller wants to find, commission, resume or review a Media or Studio work. Ordinary status/tool output belongs to its source application unless a specific media composition or expression is needed.

## Procedure

1. Name the requesting consumer, intended audience and deliverable. Record the source Owner and exact source revision for any factual statement. Avoid Studio when ordinary source-native presentation is sufficient.
2. Run `cd capabilities/media && python3 scripts/studio-agent-surface.py`. This discovers the live Studio action definitions and JSON input schemas without installing media tooling.
3. Run `python3 scripts/studio-agent-surface.py studio_production_standing --arguments '{}'` from the same directory. Inspect returned Production IDs and descriptions. The selected Production must come from the caller's real intent, not file timestamps or status ordering.
4. For that exact ID, call `studio_production_context` using its advertised schema. If the parameterized action requires `jsonschema` in a fresh Workspace, run `mise exec -- python3 scripts/materialize-python.py` and use `.venv/bin/python scripts/studio-agent-surface.py`. Do not install the JS renderer merely to read production context.
5. Read source-bound Claims, the selected Production and Outputs. Keep Production lifecycle, individual Output approval, underlying bytes, destination publication and human-response acceptance distinct.
6. For a real native-technical task, inspect `studio_processing_profiles`, select a profile by returned ID and both exact digests, and compile `studio_processing_probe_plan`. Runtime owns physical execution; output evidence only establishes the profile's declared technical predicates. Do not infer publication approval.
7. For a real equipment task, use `studio_equipment_propose`; for existing work search use `studio_creative_index_query`; for scoped creative evidence use `studio_learning_context`. These are existing source-owned actions, not new providers or registries.
8. Finish with the consumer's actual source-grounded plan or observed result; state the earliest missing precondition otherwise. Retain editable source, selected recoverable bytes and necessary receipts, not hypothetical future intermediates.

The current authority references are `capabilities/media/MEDIA.md`, `STUDIO.md`, `docs/media-model.md`, `capabilities/media/docs/capability-reference.md` and `capabilities/media/AGENTS.md`. Action schemas and production files remain the operational truth; this Skill is only navigation.
