# Portable verification handoff R1 — exact consumer boundary

**Scope:** small or medium single-subject Artifact with an optional object
contract, an already-qualified Artifact verification Profile, and the
native evidence produced by a **fresh** verification invocation.

This is not a second storage service, release gate, Profile registry, or
claims system. The target application's actual acceptance remains distinct.

## Consumer task and existing capability

A native producer may create `asset.wav` and an object contract under a
temporary Runtime Workspace. The producer's original verification request
contains absolute paths that cease to exist once the Workspace is released.

The existing `artifact_operations.portable_bundle` adapter re-verifies the
current source bytes, copies its canonical v2 Profile and current native
evidence, and emits a portable ZIP with relative member names:

- `subject/<filename>` — exact verified source bytes
- `contract/object-contract.json` — required only when bound by the request
- `profile/profile.json` — exact canonical Profile snapshot, **not** authority
- `evidence/**` — fresh native verification observations and service result
- `provenance/original-request.json` — original request, including historical
  absolute paths; **never reexecuted** at the receiving location
- `bundle.json` — minimal relative references and file identities

The receiving consumer checks all required members, checks their bytes, then
resolves the embedded Profile against the **current installed canonical Profile
authority**. It creates a new ephemeral verification request with recipient
paths and calls the existing native verification service.

## Run directly inside the Artifact Owner environment

```bash
# Producer: existing request bound to exact subject, Profile and contract.
python -m artifact_operations.portable_bundle build \
  /absolute/path/to/source-verification-request.json \
  --output /absolute/path/to/handoff.zip

# Recipient, after moving the ZIP to another location:
python -m artifact_operations.portable_bundle verify \
  /different/path/handoff.zip
```

No source Workspace, original absolute subject path or original evidence
directory is needed by the second command. The recipient **does** need the
Artifact verification service, matching canonical Profile and native format
tools installed; missing capability is not a verification PASS.

The commands report JSON status and fail with nonzero exit for rejected
packages. Builder rejects stale sources, failed/incomplete native verification,
and an already-existing output ZIP. Recipient rejects changed or missing
required members, mismatched Profile authority and mismatched original request
identity. Native re-verification is independent of the old service result.

**Evidence distinctions:**

- `build.status=PASS`: source verified and ZIP constructed at build time
- `verify.status=PASS` **and** `profileVerificationComplete=true`: recipient
  reran current native checks of content, not just archive CRC
- Not claimed: remote upload or account access, installed toolchain's full
  transitive provenance, large-file transfer through Runtime stdout, native
  target application editing, semantic user acceptance, publication

## Native regression

`tests/test_artifact_portable_bundle.py` exercises WAVE, real libsndfile/
FFprobe/SoX/FFmpeg providers, relocation with the original directory deleted,
and negative cases for changed subject/contract/Profile/provenance, and unsafe
ZIP entries. These are Artifact Owner source checks, not evidence that Google
Drive or Windows Office was accessed.

**Next consumer hard core:** publish to one authorized real destination,
read actual target bytes back, and have its native application attempt the
exact requested use. Do not add a generic registry for this.
