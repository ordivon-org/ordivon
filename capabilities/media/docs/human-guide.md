# Use Ordivon Media — human guide

Media helps people turn source-owned facts, research or ideas into **editable, understandable media**: writing, visuals, sound, video, motion and interactive works. Studio is the production capability inside Media, not a separate authority over what another Owner says is true.

## Decide whether Media is needed

| What you want | Where to start |
| --- | --- |
| Read a Runtime result, metric, browser page or ordinary tool output | Stay with that source/application Owner; Media is not required. |
| Explain an existing source fact to an audience in a designed form | Select the source revision and an intended audience; then use Media projection or Studio. |
| Make or revise a film, article, visual, sound work or interactive piece | Use a **Production** and its editable source, Claims and Outputs. |
| Check a real file's codec, sound level, timed text or editorial structure | Use an existing Processing Profile; this checks technical properties only. |
| Find an existing creative work or reusable idea | Start with the owner-native Creative Library or Creative Index; search results are navigation, not proof of available source bytes. |

## Explore an existing work (no installation required)

From the repository:

```bash
cd capabilities/media
python3 scripts/studio-agent-surface.py studio_production_standing --arguments '{}'
```

Read the returned `productions` entries: `productionId`, intent, audience, output identities and statuses. Choose the **actual work you mean**; the tool deliberately does not pick a current Production for you. For example, `runtime-introduction` has source materials under `productions/runtime-introduction/`.

Read the chosen `production.json`, `claims.json`, editable sources and selected Output records. They answer different questions:

- **Claim:** what a specific source revision permits this work to say.
- **Production:** the whole creative work and its lifecycle.
- **Asset / Blob:** a semantic role versus exact bytes and their durability.
- **Output:** one selected deliverable, which can be approved while the parent Production remains in review.
- **Receipt:** actual evidence needed by a later consumer; an existence claim or a passing tool exit code is not a publication verdict.

For an Agent-assisted detailed view of a *selected* Production, materialize dependencies if the action needs them:

```bash
mise exec -- python3 scripts/materialize-python.py
.venv/bin/python scripts/studio-agent-surface.py studio_production_context --arguments '{"productionId":"runtime-introduction"}'
```

The context is a read-only projection, not a render or publication action. Use `scripts/owner-environment doctor` when an installed tool or dependency is missing. This Python-only path avoids materializing the JavaScript renderer for a read-only context query. Use the full `scripts/owner-environment bootstrap` only when a task actually needs Node/renderer dependencies. Do not bootstrap solely to list production IDs or processing profiles.

## Inspect technical processing options

```bash
python3 scripts/studio-agent-surface.py studio_processing_profiles --arguments '{}'
```

The current source-owned families cover AV structure (FFprobe), audio loudness (FFmpeg), timeline interchange (OpenTimelineIO) and timed text (TTML/ttconv). This list shows the precise profile and adapter digests, **not** installed-tool readiness. To inspect a real artifact, select one profile and let an Agent compile its digest-pinned Runtime execution plan through the [native-processing Skill](../../../.agents/skills/media-native-processing/SKILL.md). The existing [processing reference](../processing/README.md) describes the native tools.

Technical PASS cannot approve meaning, style, licenses, human experience or publication. OTIO references media externally; it does not contain video/audio payloads or guarantee an editor's private effects survive interchange.

## Commission or revise a work

1. Name the **audience**, intended experience and concrete deliverable (article, master video, audio, caption file, still, interactive page).
2. Select the source Owner and **exact source revision** for any factual claims. If there is no production need, keep a plain source-native presentation.
3. Choose or create the relevant Production with editable medium-specific source; reuse existing tokens, Creative Library parts and proven native equipment before inventing a component.
4. Make the work, then review the **actual rendered/output bytes**: factual correctness against the Claim; medium craft against the intent; human response only when the claim depends on it.
5. Retain the selected output, provenance and recoverable canonical bytes with their natural owners. The actual destination/provider owns external publication and read-back.

For the technical vocabulary, use [Media model](media-model.md), [Studio design](../STUDIO.md), [technical baseline](technical-baseline.md), [authority](authority.md) and [storage layout](storage-layout.md). For expression ideas rather than ready-to-run programs, consult [Art & Expression research](../research/expression/README.md).

## If something does not work

- **No uniquely current Production:** select a concrete ID; do not take the most recently modified directory as intent.
- **Dependency unavailable:** run `scripts/owner-environment doctor`; install only the explicitly selected capability.
- **Source or bytes missing:** locate the claimed source revision or Blob authority and verify physical read-back before continuing.
- **QC passes, publication not ready:** identify the remaining factual, artistic, audience, rights or destination acceptance question. Do not invent an approval.
- **Old work or cache:** preserve only selected source/evidence with a real consumer; discard rebuildable local caches using the owning tool's native cleanup procedure.

For programmatic Agent instructions, use [Media Agent guide](../AGENTS.md). This page is a task guide; the existing source files and tool schemas are the technical reference.
