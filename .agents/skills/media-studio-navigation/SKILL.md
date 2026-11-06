---
name: media-studio-navigation
description: "When an Agent must decide whether Ordivon Media/Studio owns a requested human-facing output, find the real Production and source-bound Claims, or route writing, video, audio, visual and interactive work into existing Studio capabilities, follow the current Media Agent Surface and owner contracts. Not for generic tool output, running native probes without a selected file (use media-native-processing), or external publication."
compatibility: "Ordivon monorepo Media source; Python 3 for dependency-light initial discovery."
metadata:
  source-authority: "capabilities/media/AGENTS.md and current ordivon_studio.agent_surface schemas"
---

# Media Studio Navigation — route to an existing consumer

## Trigger

Use when a caller wants to understand, commission, resume or revise an Ordivon Media expression or Studio Production and needs a concrete **first action**. Source/native app observation alone does not justify Media activation.

## Actual shortest path

1. Identify user audience and intended deliverable, source Owner revision and final consumer. If the existing source/UI is already sufficient, do not invoke Studio.
2. Read `capabilities/media/AGENTS.md` and run from `capabilities/media`:
   `python3 scripts/studio-agent-surface.py`. Use the returned JSON schemas rather than a static Skill-tool list.
3. For an existing work run `python3 scripts/studio-agent-surface.py studio_production_standing --arguments '{}'`. Select **one** `productionId` by real owner/caller intent; current identity is deliberately not inferred by Studio.
4. For a selected work request `studio_production_context` with that ID; where its JSON-Schema dependency is absent, from Media run `mise exec -- python3 scripts/materialize-python.py`, then invoke `.venv/bin/python scripts/studio-agent-surface.py`. Avoid acquiring the JavaScript renderer for a read-only query. Read the linked Claim/Production/Asset/Output source and the selected source revision before making any external-world assertion.
5. Route to `studio_creative_index_query`, `studio_learning_context` or `studio_equipment_propose` only for an actual needed component. For FFprobe, FFmpeg, OTIO or TTML technical inspection hand off to `media-native-processing` with exact digest-pinned profile and source file; this Skill does not execute a probe.
6. Compose existing media/editor/native providers first, retain editable source, then actual rendered bytes and only consumer-useful evidence. Send any physical effects through Runtime; external publication and read-back stay with the destination Provider/Owner.
7. Decide against source-bound Claim, actual medium craft and, only where claimed, human-response evidence. Distinguish finished Output approval from whole Production state and provider publication. Report unknown dimensions as UNKNOWN, not a synthetic PASS.

## Boundaries / sources

- Owner responsibilities: `capabilities/media/MEDIA.md`, `STUDIO.md`, `docs/media-model.md`.
- Human route: `capabilities/media/docs/human-guide.md`.
- Native LEGO/typed representations: `capabilities/media/planning/lego-plan-r1.json`, `processing/profiles/`; never create a shadow catalog.
- Skills already installed for deeper method selection: `design-structure-matrix`, `compositional-contracts`, `recursive-lego-calculus`, `media-native-processing`.

Stop when the consumer has the actual source-grounded plan or accepted output, or the earliest missing precondition is named. Don't bootstrap the entire Studio environment for simple discovery.
