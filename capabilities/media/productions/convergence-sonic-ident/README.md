# Convergence — Ordivon Sonic Ident 001

A short procedural audio work built around a recurring Ordivon idea: multiple independent signals remain distinct long enough to preserve provenance, then converge into a stable, actionable field.

## Concept

- Three tones begin at different frequencies and stereo positions.
- Each glides toward a harmonic 220/330/440 Hz field while its pan collapses toward center.
- Four low pulses mark staged evidence arrival.
- A restrained 880 Hz cue marks the resolved/actionable state.

The piece is intentionally compact and functional rather than cinematic. It can later seed UI cues, motion idents, video title cards, or a larger `CONVERGENCE` work family.

## Editable source

`generate.py` is the canonical procedural source for the composition.

## Render chain

1. `generate.py` → 48 kHz stereo PCM source WAV.
2. SoX gain staging / 24-bit master.
3. FLAC archival copy.
4. OGG/Vorbis delivery copy.
5. FFmpeg waveform PNG for inspection.

## Truth boundary

The audio encodes a creative interpretation of Ordivon concepts. It is not a Runtime, Host, Research, or system-state authority.

## Bounded operation dependency impact (current read-only consumer)

The file `operation-lineage.json` is an opt-in, schema-validated **declared**
topology of five native processing steps: `generate-source` (script to PCM
source WAV), `master-audio` (SoX master), `encode-flac`, `encode-ogg`
and `render-waveform` (FFmpeg). Each downstream `inputFiles` now
references the actual path and SHA-256 of its selected predecessor
carrier (source WAV or mastered WAV). A false parent/input linkage is
rejected rather than treated as a valid transitive dependency. These
are current local carrier bindings, **not proof of historical provider use**.
It does **not** encode exact original
commands, build environments, automatic cache keys or historical Runtime
Job replay. The current `sourceCarrier` and `outputCarrier` byte
observations remain a separate source of physical evidence.

```bash
cd capabilities/media
uv run --frozen ordivon-studio production-context \
  productions/convergence-sonic-ident
uv run --frozen python -m unittest discover -s tests -p test_operation_impact.py -v
```

Inspect `operationLineage.steps` and `revalidateStepIds`. A source
change affects all downstream steps; a mutation of the OGG delivery carrier
affects only its selected leaf. A file unavailable for readback is UNKNOWN;
the contract never implies "unchanged" or a production/publishing failure.
`actionKey=null` and `cacheReuseAuthorized=false` until independent
hermetic recipe, qualified tool/OS environment and replay evidence exists.
The current Python source generator was independently rerun in an isolated
temporary directory under Python 3.15.1 with matching source WAV SHA-256,
but that one replay is not a cross-host proof.
