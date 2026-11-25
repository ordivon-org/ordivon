# Artifact R14 — provider convergence execution spec

Authority: existing Artifact Standing R2.1 and Host handoff #32671. Source
cut f8426d952f29aed8d4bb35c424144e87ac78bb62 plus qualified predecessor
#2773 6b37f8ba2e15f8ab98a37fcc03820a674b02864f. This is a candidate, not
production activation.

## External thought modules and adoption
- Playwright Docker: https://playwright.dev/docs/docker — client/image version
  agreement, isolated nonroot execution. Official image is not an arbitrary
  untrusted-web security guarantee.
- Podman run: https://docs.podman.io/en/latest/markdown/podman-run.1.html —
  use native immutable image selection, no pull, read-only mounts, network
  none, bounded container lifetime; no custom container scheduler.
- SLSA verification: https://slsa.dev/spec/v1.1/verifying-artifacts —
  bind evidence to exact subject and method, not a mutable tag. A digest
  commitment is not signature verification.
- Temporal: https://docs.temporal.io/activity-definition and
  https://docs.temporal.io/workflows — durable history/replay and idempotent
  Activities; never put native effects into deterministic Workflow code.

## Logic -> capability, owner boundaries

| Logic | Existing capability / contract | Decision |
|---|---|---|
| Subject commitment | artifact_core contracts/file_stream/input_snapshot | reuse exact single descriptor hash and private snapshot |
| Profile semantics | profile JSON / jsonschema | retain existing required gates |
| Dependency closure | per-family native closure; HTML setContent reads exact HTML, network disabled for OCI | bounded, no general HTML resource claim |
| Capability binding | existing profile/owner locks, current Node manifests | exact recipe identity, rolling candidate qualification |
| Provider qualification | native Podman inspect + declared OCI carrier | single explicit OCI route, no fallback |
| Build composition | DirectPython/OCI operation providers | retain actual builders |
| Native verification | Playwright/axe, vnu, OpenXML, qpdf, OCCT, Khronos and family tools | no custom replacement engines |
| Evidence normalization | existing web browser transport and stage gates | one report format; unknown on operational failure |
| Standing decision | shared claim coverage / native identity | no new decision authority |
| Provenance binding | FileCommitment, existing receipts, in-toto/SLSA | exact subject and method identities |
| Trust qualification | existing Sigstore policy | separate from native PASS |
| Package composition | OCI layout/referrers | reuse existing publisher |
| Target materialization | existing delivery adapters | owner-specific |
| Consumer acceptance | target/domain readback | not inferred from local verification |
| Lifecycle handoff | existing Temporal / Runtime / Host | native retries, no duplicate orchestration |
| Outcome resolution | explicit observation/standing/consumer levels | UNKNOWN remains UNKNOWN |

## R2.1 narrow provider operation
I: explicit owner opt-in, admitted HTML, locked image manifest/config identity,
source Node lock metadata and runner; O: existing native report plus provider
binding and scoped diagnostics; S: ephemeral private input snapshots, existing
OCI image store; pre: local image identity, source/install lock metadata
agreement, exact subject/runner staging; post: same existing consumer report
shape, method version match; inv: no fallback, no image pull, no false native
negative on unavailable transport, no implicit release; eff: one isolated
Podman container; c: O(subject+runner+lock bytes) plus native browser work;
epsilon: not complete installed Node content attestation, not process readset
or same-principal mutation proof, not arbitrary HTML safety, not deployed
origin/target acceptance; prov: exact source, image ID/manifest, lock and
runner digest, native report; unfold: provider -> invocation -> report ->
existing gate projection.

P0: reconcile #2767/#2773, exact normal queue; replace host-only web route
with explicit owner-selected OCI provider, no automatic fallback, native
positive/negative and unavailable controls. P0: qualify actual Temporal
development-only workflow and managed carriers; canonical source sync is
shared owner coordination (no forced update). P1: independent native test lane
and GLB rich-resource closure; P2: retire old host-only path only after actual
consumer transition. Keep mixed provider diagnostic donor out of production.
No release or service restart without actual deployment qualification.

## Qualified R14 slice and remaining scope

The actual public verify_web_local entrypoint selects one explicitly requested
provider; legacy host remains the compatibility default until the installed
consumer is qualified. OCI admission binds the exact local image ID + manifest,
three Node lock metadata files, runner and subject snapshots, and retains the
actual Podman options. Reject unknown provider, malformed image lock, mismatched
metadata/image, stale subject, duplicate JSON members, mismatched method versions,
incomplete selected native engine observations and inconsistent axe counts.
Method and subject binding are separate. Actual DirectPython stage consumes
browser receipts without declaring unexecuted delivery gates complete.
No production systemd authority or universal untrusted-HTML sandbox claim.

Native R14 .NET SDK source-link observation: ambient Git HEAD in DLL and path/
URL in PDB were not declared recipe inputs. The separate OpenXML candidate
disables ambient SCM queries and SourceLink for copied source only; explicit
recipe/source commitments remain. Native cross-Git-context equality and frozen
method corpus are required, not source-string tests. Local development Temporal
workflow uses actual four activities and OCI package; unsigned, never release.
