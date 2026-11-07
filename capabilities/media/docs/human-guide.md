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
OTIO and TTML work through source-pinned `mise + uv tool run` wrappers on
selection; missing global `otiotool` or `ttconv` commands are not by themselves
a failure. Check the selected Runtime Job and receipt for actual tool readiness.

Technical PASS cannot approve meaning, style, licenses, human experience or publication. OTIO references media externally; it does not contain video/audio payloads or guarantee an editor's private effects survive interchange.

## Two exact, runnable inspection/recovery examples

After explicitly materializing the pinned Python toolchain above, inspect an
existing video file without modifying it:

~~~bash
.venv/bin/ordivon-studio probe productions/live-relay-001/render/live-relay-001-source.mp4
~~~

This returns the exact Blob digest and FFprobe-observed streams. It is not
authorization to change source media or publish the Production.

For a selected Blob you actually need to preserve or recover, use the existing
CLI; these commands are **effectful** and require a chosen destination:

~~~text
.venv/bin/ordivon-studio hash <selected-file>
.venv/bin/ordivon-studio archive <selected-file> --cache-root <selected-CAS-root>
.venv/bin/ordivon-studio materialize <sha256:digest> <destination> --cache-root <selected-CAS-root>
~~~

The external Cloudflare R2 adapter is optional; inspect
`.venv/bin/ordivon-studio r2 --help` only when an actual recovery consumer
requires it. Neither the CAS nor R2 replaces the editable Production source.

## Commission or revise a work

1. Name the **audience**, intended experience and concrete deliverable (article, master video, audio, caption file, still, interactive page).
2. Select the source Owner and **exact source revision** for any factual claims. If there is no production need, keep a plain source-native presentation.
3. Choose or create the relevant Production with editable medium-specific source; reuse existing tokens, Creative Library parts and proven native equipment before inventing a component.
4. Make the work, then review the **actual rendered/output bytes**: factual correctness against the Claim; medium craft against the intent; human response only when the claim depends on it.
5. Retain the selected output, provenance and recoverable canonical bytes with their natural owners. The actual destination/provider owns external publication and read-back.

For the technical vocabulary, use [Media model](media-model.md), [Studio design](../STUDIO.md), [technical baseline](technical-baseline.md), [authority](authority.md) and [storage layout](storage-layout.md). For expression ideas rather than ready-to-run programs, consult [Art & Expression research](../research/expression/README.md).

## What formal verification does and does not guarantee

Media's native Processing Profile admission has an owner-scoped Lean model,
explained in [formal evidence](../formal/README.md). It proves abstract
admission and separation of technical QC from publication approval; it does
**not** prove the Python runtime, actual tool behavior, or rights/creative
acceptance. Inspect the real producer and the selected Runtime evidence for
those questions. A model PASS is not a production release receipt.

## If something does not work

- **No uniquely current Production:** select a concrete ID; do not take the most recently modified directory as intent.
- **Dependency unavailable:** run `scripts/owner-environment doctor`; install only the explicitly selected capability.
- **Source or bytes missing:** locate the claimed source revision or Blob authority and verify physical read-back before continuing.
- **QC passes, publication not ready:** identify the remaining factual, artistic, audience, rights or destination acceptance question. Do not invent an approval.
- **Old work or cache:** preserve only selected source/evidence with a real consumer; discard rebuildable local caches using the owning tool's native cleanup procedure.

For programmatic Agent instructions, use [Media Agent guide](../AGENTS.md). This page is a task guide; the existing source files and tool schemas are the technical reference.

## Optional DaVinci Resolve native editing

Use [Resolve's installed native API](resolve-native.md) in the approved interactive
Windows session. The previous embedded Ordivon menu Runner and CLI staging
bridge are retired. An independent OTIO probe does not prove a Studio edit.
## Produce an editable native Resolve cut

With selected local source media and a logged-in Resolve session, invoke
`scripts/resolve-native-produce.py --visual SOURCE --audio VOICE --output-dir OUT --name CUT`.
Repeat `--visual` for sequential scenes; add `--grade-saturation` to apply
Resolve's actual Color CDL. Outputs: `.mp4`, editable `.drp`, and digest receipt.
Read the exact invocation, session requirements and optional preview flags
in [Resolve native production](resolve-native.md). For new shots or more
complex Fusion/Fairlight work, extend the project with official Resolve APIs
instead of introducing another Ordivon menu Runner.

## Human: one production, one native editing workflow

Select the actual `productionId` and Claims first. Use
[Resolve-native execution](resolve-native.md) with `--visual` for consecutive
source shots or `--otio` for an existing editorial cut; the two are mutually
exclusive. In either case, you may attach a separately selected `--audio`,
apply a measured CDL saturation operation, and request a minimum timeline
length. Preserve the resulting **editable DRP** as well as the delivered MP4.

For captions, review the source TimedText cues, then use the pinned
`ttconv`/TTML processing profile to derive SRT or WebVTT. For a Remotion
animation, edit the existing React/SVG composition and render only the
selected output; import it into Resolve as visual media if appropriate.
For sound, review Fairlight's actual mix, run the existing FFmpeg loudnorm
profile on the selected audio master, and listen to the final rendered output.
For technical video QC, invoke the existing FFprobe/FFmpeg profile. A measured
codec or loudness PASS does not mean the cut is good or correctly subtitled.

For publication, identify the destination's real provider/API and read back
the posted object or receipt. Production, Output, Blob and provider publication
are separate states. Use the existing Creative Library index for discovery
and `assets.py`/selected CAS or R2 for recovery, never as extra editorial
truth stores. Discard unselected preview renders and scratch once no consumer
references remain; do not delete masters or system directories by name alone.

## Human: applying and evaluating a precise native grade

Use the supported `--grade-slope`, `--grade-offset`,
`--grade-power` and `--grade-saturation` inputs with
`scripts/resolve-native-produce.py` for an isolated Resolve
project. They map directly to the official Color CDL operation.
Read `gradeCDL` in the receipt, inspect the real render on a
calibrated display appropriate to the selected output, and retain
the editable DRP. The receipt also shows which files Resolve
actually loaded into its video and audio tracks. Source digest
verification and independent FFprobe observations cannot
substitute for creative color review or published-platform
readback. No approval is manufactured by the script.

## Parameterized Remotion from existing components

The source-owned \`runtime-flow\` Composition accepts JSON input props
\`eyebrow\` and \`headline\` (defaults retained in \`src/runtime-flow-composition.tsx\`).
When only title copy changes, do not fork the React/SVG layout or duplicate
timeline data. Select a Production and approved copy; write a small \`props.json\`,
then from \`capabilities/media/apps/motion-remotion\` run:

\`\`\`bash
pnpm exec remotion render src/index.ts runtime-flow /tmp/selected-animation.mp4 \\
  --config=remotion.config.ts --props=/tmp/props.json
\`\`\`

The JSON file can contain \`{"eyebrow":"Media","headline":"A selected\\nmessage"}\`.
Use \`pnpm tokens:build\` from the Media root beforehand. The renderer
owns animation frames and timing, while the exact output bytes and
source/props digests must be reviewed before attaching an Output.
The existing Production Claim remains the authority for factual words.
