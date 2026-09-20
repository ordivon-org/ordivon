# runtime-introduction timed-text migration bridge

This directory is migration evidence, not the current timed-text authority.

One legacy-only export was performed from the historical Ordivon JSON cue document into WebVTT. The resulting VTT was then consumed by pinned external `ttconv==1.2.3` to create the standard TTML source. Subsequent VTT/SRT delivery forms are generated from TTML through ttconv.

- legacy JSON: `sha256:a6d515aa8e2aabeec7db6a832dd2d8a63c814ae10b7c474b808174e1fd47ba74`
- one-time legacy-export VTT: `sha256:5223ee91eb9625ad9ee6fda5a8bd26ba685354af17c9e0da43d591ab73db7eb9`
- standard TTML: `sha256:b30e5f65c5fc13d3fa3783ea23f5fe1d10591a2c52d3ede9c257b0c0be39e909`
- derived WebVTT: `sha256:8673c412f57823067035e25879fd4f828e5afcee9f2c38288c75276b5fa5d35b`
- derived SRT: `sha256:e9d517c8bdf3bc8de964dee19901bf518e5358b0bb1e09054cb650efe96995a4`

Direct bridge-VTT -> SRT and bridge-VTT -> TTML -> SRT were byte-identical during R4. This proves bounded equivalence for this production only; it is not a universal-losslessness claim across timed-text formats.
