# Artifact E2E — Audio / Ogg Vorbis R1

## Standing

`SHADOW_PROFILE_LOCAL_LIVE_PROVEN_WITH_TARGET_SAMPLE_BOUNDARY_DIVERGENCE`

R1 covers one bounded browser/game interchange case: one non-chained Ogg logical stream containing Vorbis version 0 audio, served as `audio/ogg; codecs=vorbis`. Container semantics follow RFC 3533; media-type identity follows RFC 5334; codec and granule-position semantics follow the Xiph Vorbis I specification.

The profile deliberately separates **standard/reference semantics** from **target implementation behavior**. Xiph `ogginfo` + `oggdec` establish the reference Ogg/Vorbis view and exact playback sample boundary. FFprobe/FFmpeg provide an independent technical/decoder observation. Pinned Chromium and Firefox are real browser target observations through Web Audio `decodeAudioData`.

## Current Game pressure test

At Game revision `809a82b733e3b3c761847a72a6a7fb7a94502ae5`, all three Station Zero cues pass the bounded Ogg/Vorbis profile. The target matrix consistently exposes one interoperability fact:

- Xiph `oggdec` and Firefox return the contracted granule/playback boundary;
- FFmpeg and Chromium return exactly 128 fewer samples per channel;
- at 48 kHz the difference is approximately 2.667 ms.

This divergence is retained as evidence. Artifact does not redefine the Vorbis standard around Chromium, and it does not decide whether a 2.667 ms cue boundary difference is acceptable to Game.

## Acceptance boundary

Profile PASS requires:

- one completed Vorbis logical stream accepted by Xiph `ogginfo`;
- version 0, contracted rate and channel topology;
- Xiph reference decode sample count equal to the object contract;
- FFprobe independent Ogg/Vorbis duration/rate/channel agreement;
- successful FFmpeg independent decode with a numerically compatible common PCM prefix;
- successful pinned Chromium and Firefox decoding at the contracted rate/channel topology.

Browser sample-count equality is **reported, not required for standard PASS**. A consumer that requires sample-exact cross-browser duration must add that requirement at the consumer/target acceptance layer.
