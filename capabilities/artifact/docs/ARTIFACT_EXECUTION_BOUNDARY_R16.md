# Artifact R16 — execution authority and test-lane convergence

Extends Standing R2.1, Provider R14, Production R15, Host #32786. This is a
bounded candidate, not production provider activation. Base 51f78bc50a09af584f47fb7b2ceef201ee87d5dc.

## Thought modules
- systemd native responsibility-specific isolation: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec
- Podman API authority is full access as the service user, not a constrained
  browser-verification API: https://docs.podman.io/en/latest/markdown/podman-system-service.1.html
- Temporal Activities / idempotent operations: https://docs.temporal.io/activity-definition
- pytest native markers and real consumer tests: https://docs.pytest.org/en/stable/example/markers.html
- warcio and warcio.js streaming readers, Python hashlib and Node crypto:
  https://github.com/webrecorder/warcio and https://github.com/webrecorder/warcio.js

## Logic / capability owner mapping
The 16 R14 business logic modules and 12 R15 release logic modules remain
authoritative. Refine the following intersections, not new registry owners.

| Logic | Existing capability | Decision |
|---|---|---|
| Source admission/materialization | Git ff-only | small clean deltas, independent loaded service identity |
| Subject and method identity | file commitments, locked uv, native reports | preserve historical evidence, record current bytes separately |
| Profile semantics / closure | existing profiles and JSON Schema | no reduced required gate |
| Provider qualification | Podman, systemd, Runtime | effect authority distinct from Workflow |
| Build composition | existing DirectPython / OCI | retain one operation contract |
| Native verification | managed warcio, native streaming warcio.js, Playwright, OpenXML, OCCT | reuse, no second parser |
| Evidence normalization | existing raw receipts | separate observation from standing |
| Standing / provenance / trust | existing shared logic, OCI/in-toto/SLSA/Sigstore | unavailable transport UNKNOWN, no historical proof laundering |
| Packaging / materialization / consumer | existing OCI and consumer readback | no local PASS to release inference |
| Lifecycle / outcome | Temporal, Runtime, Host | durable receipt and explicit authority |
| Verification | pytest integration marker, Ruff, finite models | one suite, portable and native lanes |
| Retirement | existing owner lifecycle | no deletion before consumer migration |

## Effect delegation boundary
Observed production-like one-shot unit with existing systemd restrictions
cannot inspect rootful Podman image: storage.lock read-only, exit 125.
No existing bounded Runtime client inside Artifact Worker was established.
Prefer existing Runtime-owned exact operation execution where authority
and input commitments are available. Temporal remains durable lifecycle
authority; a dedicated native Activity route is an alternative only with
explicit qualified task queue, historical replay compatibility, bounded
operation contract and actual consumer. Do not expose a root Podman socket,
disable Worker protections, or silently choose host browser.

I=(artifact commitment, profile, explicit provider, qualified execution
authority, operation identity); O=(native raw report, receipt, standing);
pre=exact source and installed method, authenticated execution admission,
explicit effect route; inv=no fallback, no release from raw PASS, no new
execution owner; eff=bounded local OCI process; post=transport and native
evidence readback; epsilon=not arbitrary HTML safety, not complete readset;
prov=source, method, input, raw result, runtime receipt.

P0 queue #2767/#2773/#2824 normally; after predecessors merge, rebase provider
delta only (38172245). Prove actual bounded Runtime/Temporal integration
before production default activation. Keep direct same-sandbox refusal.

## Test partition and WARC migration
- Queue delegates to one portable verify recipe. Workstation-only tests
  use existing integration marker, not duplicated filename exclusions.
  Native task runs actual tools; no unconditional skip to hide failures.
- Split CAD Agent semantic scope from native presence. Preserve malformed
  input tests in portable lane. Message/WARC live dual-parser tests native.
- Switch WARC Python parser/checker to already locked managed warcio
  (actual 1.8.2); do not mutate sys.path. Use isolated Python CLI invocation,
  observe loaded module identity and distribution version, not claim full
  package attestation. Use incremental SHA-256 for Python and native JS
  decoded content iteration; file digests stream. Retain old 1.8.1
  historical binding unchanged. No universal memory bound (record metadata,
  native parser decompression and native integrity checker separate).
- Actual first native lane 51 PASS/3 FAIL: old Assimp/Blender/Godot and GDAL
  shadow binding current-file comparisons drift. Preserve failures and old
  proof until fresh native current method qualification; no replace old
  digests with current bytes without exact native witness. Rich GLB closure
  still pending. Independent current method receipts and historical
  reproduction are distinct obligations.
- Native restored Office/STEP/message/WARC/CAD tests 31 PASS. WARC red
  global import mutation + unbounded read -> new bounded-read control and
  actual 3+ MiB dual-parser digest parity; scoped 10 PASS.

No production source installation from this candidate. R15 current Python,
OpenXML and Worker remain production until ordinary merge + deployment.
