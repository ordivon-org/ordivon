# Media R15 — consumer-bound native and stateful verification
Extends R14 #32823/#32872 and R15 Host #32905, coordination #32891.
Preserve L01–L13 and verification V01–V10. No new test service.

## P0: Native selected audio observation
I physical media, selected audio ordinal and explicit profile.
O native observations and mechanical verdict with strict JSON.
S private temporary statistics directory, no production mutation.
pre valid ordinal and existing provider capability.
post structure and loudness refer to same ordinal; permuting streams
and adjusting ordinal preserves observed measurement.
inv missing/invalid index cannot yield measured loudness; nonfinite
observations cannot serialize as non-JSON numeric literals, and required
nonfinite integrated/peak cannot pass.
eff one FFmpeg analysis, no normalization output, source unchanged.
c replace stderr slicing by native stats_file; no extra pass or dependency.
epsilon native FFmpeg version must support stats_file; no claim of complete
environment identity or perceptual/publication qualification.
prov real dual-track CLI differential test, direct native stats oracle,
stream permutation, strict JSON parsing, original source SHA.
unfold FFprobe -> select ordinal -> native FFmpeg -> typed observation -> verdict.
Existing internal numeric API retains IEEE nonfinite observations; only
wire representation normalizes finite/null with explicit standing.
Shell native adapter still independently invokes the same mature FFmpeg
capability; no claim of one shared cross-language application wrapper.

## P1: Archived Runtime demonstration trace consumer
I v1 schema-valid observation sequence, identity and progress.
O internal consistency only, not live Runtime truth.
S test-only fixture/replay; pre historical v1 contract.
post valid monotone trace accepted, corrupt coordinates rejected.
inv same attempt, fixed total, monotone counters and terminal consistency;
duplicate observations permitted by historical contract.
eff read-only; c bounded Hypothesis stateful sequences; epsilon no claim
of native PG or OS effects; prov independent model and controlled mutants.
unfold generate operations -> schema -> actual consumer -> independent oracle.
Do not impose today's Runtime state machine on archived presentation data.

## Integration
Keep root lightweight and strict PG/native qualification distinct. Request
actual root owner consume strict gate with native prerequisites; no parallel
root CI or toolchain writer. Use exact frozen development lock from #2835
for stateful tests; no new production dependencies. Coverage is diagnostic,
not an approval threshold. References: https://ffmpeg.org/ffmpeg-filters.html
https://hypothesis.readthedocs.io/en/latest/stateful.html
https://json-schema.org/understanding-json-schema/reference/type
