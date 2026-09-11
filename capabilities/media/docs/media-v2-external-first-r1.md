# Media v2 external-first migration — R1

## Decision

Construct Media v2 as an external-tool composition plus a minimal Ordivon evidence/control plane. Do not refactor the legacy Studio implementation into v2. Migrate old code only when an external composition demonstrably cannot preserve a required Media semantic.

## First admitted vertical slice

```text
exact artifact bytes
  -> FFprobe raw JSON
  -> explicit AV profile assertions
  -> digest-bound external QC evidence
```

The slice is deliberately independent of the legacy Python media stack. It proves only mechanical profile facts. It does not claim semantic correctness, aesthetic quality, rights clearance, accessibility outcome, review acceptance, publication, or destination currentness.

## Destructive acceptance

`media-v2/tests/smoke.sh` generates two files using FFmpeg:

1. a 1920x1080, 30 fps, H.264, yuv420p, BT.709, no-audio positive fixture that must pass;
2. a 1280x720 otherwise-equivalent negative fixture that must fail closed on width and height.

A passing positive without a rejecting negative is not sufficient evidence.

## Legacy retirement map

| Legacy area | R1 disposition | External-first target |
| --- | --- | --- |
| `assets.py::probe_media` | retirement candidate | FFprobe + later MediaInfo |
| `qc.py::validate_video_probe` | retirement candidate | declarative profile assertions over external probe evidence |
| `video.py` normalization logic | later compression | FFmpeg profile invocation |
| `perception.py`, signal portions of `rich_perception.py` | later replacement | FFmpeg/QCTools/VMAF |
| `timed_text.py` interchange/export | later replacement | TTML/IMSC/WebVTT tooling |
| `review.py` playback/perception packet | later reduction | xSTUDIO/OpenRV/Kitsu + digest-bound ReviewDecision |
| `resolve_adapter.py` | retain only proven delta | OpenTimelineIO adapters + private-delta evidence |
| `assets.py` local CAS | later retirement | DVC/ORAS/object storage depending lifecycle |
| `distribution.py` static carrier profiles | retirement target | provider-native APIs/OpenAPI/connector observations |
| `distribution.py` plan/effect/readback separation | semantic retention | thin contract/policy layer |

## Graduation sequence

R1 technical probe -> R2 real `runtime-introduction` master -> R3 timed-text/OTIO migration -> R4 asset authority migration -> R5 external review consumer -> R6 provider-native distribution/readback -> legacy deletion proof.

No legacy implementation is admitted into v2 merely for parity convenience.
