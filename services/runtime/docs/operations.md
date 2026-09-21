---
schema_version: 1
id: runtime.operations
title: Runtime Operations
type: operations
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-runtime
audience:
  - operator
  - builder
  - agent
updated: 2026-09-11
summary: Canonical deployment, health, capacity, Workspace lifecycle, reclaim, rollback, and operational verification contract.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-runtime
related:
  - runtime.model
  - runtime.recovery
  - runtime.authority
---
<!-- cspell:words aria2c hyperfine libexec nocapture nonselected rclone rsync toplevel -->

# Runtime Operations

## Scope

This document owns the operational path for local deployment, health inspection, capacity acceptance, Workspace lifecycle, reclaim, cache hygiene, rollback, and contained-local acceptance.

Runtime operations stop at physical execution and Workspace state. They do not assess Host Task completion, resume a Harness Run, invoke a Provider, or decide whether domain evidence is sufficient. Use Host operations for Journal/CAS and Task reconciliation, and Harness operations for Assignment/Run recovery.

## Normal operation

Operate through the receipted service, bounded health path, configured lifecycle timers, explicit Workspace ownership, and the canonical deployment scripts described below. Frequent automation should use the fast health path rather than maintenance scans.

## Failure detection

Treat unhealthy service state, unresolved Registry conditions, held reservations, orphan directories, dirty or active Workspaces, digest mismatches, failed cache cleanup, and deployment-receipt mismatch as explicit operational signals rather than inferred success.

## Recovery

Recover through Runtime reconciliation, documented repair or quarantine paths, explicit Workspace close/reclaim operations, and receipt-bound Git rollback. Never delete live state or redispatch ambiguous work as a substitute for diagnosis.

## Verification

Use service status, Runtime doctor and inspect commands, capacity acceptance, lifecycle receipts, contained-local acceptance, deployment manifests, and the repository test suite. The architecture is defined in [`runtime.md`](runtime.md), focused repair guidance is in [`recovery.md`](recovery.md), and exact command sequences and acceptance conditions follow in the detailed sections.

Operational tools are narrow wrappers around existing truth owners. They do not create a second deployment database, scheduler, Workspace lifecycle service, or Python-side interpretation of Runtime Registry tables. Registry-backed operator facts are projected by Rust Core through `ordivon-runtime-inspect`; physical SQLite backup/restore remains a separate storage operation.

## Prefer mature host utilities

Do not recreate mature file transfer, structured-data filtering, archive, media, PDF, database, GitHub, or benchmarking behavior in one-off Python or shell scripts. Use the installed host utility through `workspace.exec` or `workspace.execPlan` with an absolute executable and explicit arguments. Runtime owns admission, execution, observation, cancellation, evidence, and process state; the utility remains responsible for its own operation semantics.

The canonical Arch WSL workstation currently provisions the following additional utilities:

```bash
pacman -S --needed aria2 rsync yq hyperfine rclone
```

These packages are host capabilities, not mandatory Runtime server dependencies and not additional MCP Tools. Query their live paths and versions before a version-sensitive operation rather than copying version claims into durable documentation.

| Need | Preferred utility | Operational rule |
| --- | --- | --- |
| repository and text search | `/usr/bin/rg`, `/usr/bin/fd` | Prefer them over recursive `grep` and complex `find` expressions. |
| JSON and YAML inspection | `/usr/bin/jq`, `/usr/bin/yq` | Use jq-style queries. Do not rewrite comment- or formatting-sensitive YAML with `yq`; use a parser or an exact text patch. |
| ordinary API calls and small probes | `/usr/bin/curl` | Keep API requests and bounded health probes on `curl`; do not substitute a download manager for protocol-aware application calls. |
| large or interruption-prone HTTP downloads | `/usr/bin/aria2c` | Enable continuation and write to an explicit destination. Prefer this over custom retry loops and partial-file scripts. |
| local or SSH directory copying | `/usr/bin/rsync` | Preserve trailing-slash intent. Use `--dry-run` before any deletion-capable invocation; never add `--delete` by default. |
| remote or object-storage transfer | `/usr/bin/rclone` | Start with `copy` and verify with `check`. Treat `sync` as deletion-capable and require explicit target semantics. Installation does not configure a remote. |
| archive inspection and creation | `/usr/bin/7z`, `/usr/bin/bsdtar`, `/usr/bin/zstd` | Prefer mature format support over new `zipfile` or `tarfile` scripts unless product code genuinely requires a library API. |
| repeatable command benchmarks | `/usr/bin/hyperfine` | Use warmups and multiple runs; use `--shell=none` when shell behavior is not part of the measurement. |
| media inspection | `/usr/bin/ffprobe` | Request JSON output instead of parsing human-oriented FFmpeg logs. |
| PDF inspection and text extraction | `/usr/bin/qpdf`, `/usr/bin/pdfinfo`, `/usr/bin/pdftotext` | Use `qpdf --check` for structural validity and the Poppler tools for metadata or text. |
| SQLite physical administration and GitHub operations | `/usr/bin/sqlite3`, SQLite backup API, `/usr/bin/gh` | Use direct SQLite only for physical backup/restore/integrity operations. Runtime Registry semantics are consumed through `ordivon-runtime-inspect` projections rather than ad hoc queries; use the official GitHub CLI for GitHub operations. |

Typical invocations are intentionally thin:

```bash
/usr/bin/aria2c --continue=true --dir "$destination" --out "$name" "$url"
/usr/bin/rsync -aH --partial --info=progress2 "$source/" "$destination/"
/usr/bin/yq -r '.runtime.preferred' configuration.yaml
/usr/bin/hyperfine --warmup 3 --runs 10 --shell=none '/absolute/command'
/usr/bin/rclone copy "$source" remote:path
/usr/bin/rclone check "$source" remote:path
```

Do not add a Runtime wrapper or MCP projection merely to rename one of these commands. Add a narrow adapter only after repeated real failures show that callers cannot safely express the operation through explicit arguments, or when structured effect semantics must be enforced rather than merely documented.

## Encrypted credential provisioning

Runtime does not invent a secret store. Linux credential decryption is owned by systemd. Create one operator-only authority directory, encrypt each credential before placing it there, and configure only the authority root plus the authenticated Runtime principals allowed to use it. For a host-key-backed credential on a machine whose systemd credential key has already been initialized, a minimal provisioning flow is:

```bash
install -d -m 0700 /var/lib/ordivon/credentials/finance-provider
umask 077
printf '%s' "$PROVIDER_API_KEY" | systemd-creds encrypt \
  --with-key=host \
  --name=api_key \
  - \
  /var/lib/ordivon/credentials/finance-provider/api_key
unset PROVIDER_API_KEY
```

Do not put the plaintext in the Runtime environment file. Configure the authority itself in the Runtime environment file, for example:

```text
ORDIVON_CREDENTIAL_AUTHORITIES_JSON=[{"name":"finance-provider","root":"/var/lib/ordivon/credentials/finance-provider","allowedPrincipals":["principal:local-owner"]}]
```

`allowedPrincipals` is mandatory and non-empty. Runtime checks that authenticated principal before object resolution. `runtime.describe` intentionally exposes only the configured authority names. New credential-bound execution accepts only an authority name and credential name; systemd receives the Job-owned encrypted snapshot through `LoadCredentialEncrypted=` and exposes decrypted files below `CREDENTIALS_DIRECTORY`.

Rotation is replacement plus a new Runtime request identity: write a newly encrypted blob to the authority under the same logical credential name, then admit a new `workspace.execCredentialBoundTrusted` request. Replaying the old `clientRequestId` must return the historical Job/result without reopening the authority, even after Runtime restart. Durable terminal Jobs do not retain their encrypted snapshot; periodic Runtime reconciliation removes it without a secret-specific TTL.

Host-key encryption is a deployment choice, not a universal security claim. Verify the protection of `/var/lib/systemd/credential.secret` and its backing storage on the actual host. If policy requires TPM2-bound credentials, provision and qualify that systemd mode separately before claiming it; do not infer TPM protection from successful `systemd-creds encrypt --with-key=host`. Root and the service authority remain outside this confidentiality boundary.

## Local deployment

`scripts/ordivon-runtime-deploy` replaces the ad hoc deployment shell used during development. It has four commands:

```text
prepare   materialize one exact Commit and write a digest-bound release manifest
plan      read-only eligibility and installed-artifact report
apply     lock, retain previous artifacts, install, restart, probe, receipt
rollback  restore the exact previous artifact set from one receipt
```

A normal production deployment is run from the Runtime owner root. The owner root may itself be
the Git top-level (standalone checkout) or a real subdirectory of a containing monorepo such as
`services/runtime`. Release identity remains the containing Git Commit; Runtime artifacts and policy
are materialized only from the configured owner root inside that exact detached Commit.

```bash
source=$(pwd -P)
test -f "$source/Cargo.toml"
test -x "$source/scripts/ordivon-runtime-deploy"
commit=$(git -C "$source" rev-parse HEAD)
candidate="$source/target/ordivon-release-candidates/$commit/release"
manifest="$candidate/ordivon-deployment-manifest.json"
cargo=$(command -v cargo)
test -x "$cargo"

scripts/ordivon-runtime-deploy prepare \
  --source-repo "$source" \
  --commit "$commit" \
  --candidate-dir "$candidate" \
  --candidate-manifest "$manifest" \
  --cargo "$cargo"

scripts/ordivon-runtime-deploy plan \
  --source-repo "$source" \
  --commit "$commit" \
  --candidate-dir "$candidate" \
  --candidate-manifest "$manifest" \
  --install-dir /usr/local/libexec/ordivon \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --env-file /etc/ordivon/ordivon-runtime.env \
  --receipt-root /var/lib/ordivon/deployments \
  --expected-tool-count 23 \
  --pretty

scripts/ordivon-runtime-deploy apply \
  --source-repo "$source" \
  --commit "$commit" \
  --confirm-commit "$commit" \
  --candidate-dir "$candidate" \
  --candidate-manifest "$manifest" \
  --install-dir /usr/local/libexec/ordivon \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --env-file /etc/ordivon/ordivon-runtime.env \
  --receipt-root /var/lib/ordivon/deployments \
  --expected-tool-count 23 \
  --drain-seconds 30
```

The default production release has one artifact authority rather than separate binary and operator-script installations. It contains **12 receipt-bound artifacts**: five Rust binaries, the six installed Runtime operator executables (`deploy`, `lifecycle`, `reclaim`, `cache`, `status`, and `capacity-acceptance`), and their shared `mcp_probe.py` support module. Every artifact is bound by name, kind, byte length, SHA-256 digest, and canonical mode (`0755` for executable artifacts and `0644` for `mcp_probe.py`). The same exact-commit candidate manifest also binds the non-secret `defaultRuntimeMs` / `maxRuntimeMs` Job-timeout policy extracted from `packaging/systemd/ordivon-runtime.env.example`; these values are part of the full release transaction even though the environment file itself remains installation-owned and may contain unrelated credentials, paths, and settings. Repository-owned systemd units and the Windows launcher are installation/provider concerns outside this contracted Runtime release set; changing either requires its own operator-owned update rather than being smuggled into an ordinary Runtime self-release. Passing explicit `--binary` values intentionally selects a binary-only subset for focused testing or exceptional maintenance; it is not the canonical production release set and does not manage Runtime timeout policy.

Eligibility requires:

- the exact requested Commit can be materialized from the Git repository containing `--source-repo`;
- `--source-repo` is a real Runtime owner directory, never a symlink; it may equal the Git top-level or be a descendant such as `services/runtime`;
- `prepare` resolves the containing Git top-level plus the owner-relative path, constructs a temporary detached checkout of that exact Commit, then builds and stages only from the corresponding Runtime owner directory. Mutable checkout state, including Git index flags such as `assume-unchanged`, therefore cannot enter the candidate;
- the detached release source remains clean after the build;
- the explicit required ref (by default `origin/main`) remains the publication authority. For a standalone Runtime owner it must resolve to the requested Commit exactly. For a Runtime owner nested beneath a containing monorepo, the requested Commit must be an ancestor of the required-ref Commit and the Runtime owner tree at both Commits must be byte-identical; unrelated commits outside the Runtime owner therefore do not invalidate a candidate, while rewritten ancestry or any Runtime-owner change fails closed. Local `HEAD` and dirty state remain diagnostics and never become release authority;
- the candidate manifest binds the exact source repository, Commit, `sourceMaterialization=detached_git_checkout`, candidate directory, complete release artifact set, modes, sizes, digests, and for a full release the positive `defaultRuntimeMs <= maxRuntimeMs` timeout policy extracted from that exact source;
- the candidate manifest binds the Cargo/rustc invocation paths, their resolved launcher SHA-256 digests, version output, and Rust host target; proxy invocation paths such as rustup's `cargo`/`rustc` symlinks are preserved during the build;
- `plan` verifies the complete candidate-manifest digest before installation eligibility is reported;
- every candidate artifact and currently installed artifact is a regular file and every executable-mode artifact is executable;
- `plan` reports any active or held Job (except a provable deployment Job) as an eligibility blocker; `apply` may proceed past that single blocker only to stage a reversible candidate and acquire the Registry admission fence, then it must drain those Jobs naturally within `--drain-seconds`;
- the confirmation commit exactly matches the requested commit.

Runtime startup does not run an unbounded reconciliation scan before binding MCP ingress. Core construction performs the recovery that must precede serving (including recoverable orphan/input ownership convergence); after the listener is established, the existing maintenance loop fires immediately and processes recovery-required, held-orphaned, and other nonterminal Attempts in operator-bounded batches (`ORDIVON_RECONCILE_BATCH_SIZE`, default 32). Registry history size therefore does not gate socket readiness.

The tool first stages receipt-local previous artifacts without replacing the running release. It then takes an exclusive Registry `admission.lock`. Runtime new admission takes a shared lock only after exact replay has been checked, so a deployed Runtime returns retryable `DEPLOYMENT_IN_PROGRESS` for new work while already committed requests remain replayable. Under the exclusive fence, `apply` waits for active/held reservations to drain naturally and then stops MCP ingress immediately. It rechecks the Registry with ingress closed, reruns the complete deployment plan, and writes that final plan to the receipt before any release replacement. Only then are `.next` / `.previous` install artifacts staged. For a full release, the deployer verifies that the two timeout-policy keys still match the pre-drain observation, atomically updates only those keys in the installation-owned environment file, and then commits the staged Runtime artifact set below `--install-dir`; unrelated environment lines are preserved. If the post-commit probe fails, the deployer re-observes the Registry migration version before choosing any binary rollback. Automatic restoration of the receipt-local previous Runtime artifact set and previous timeout-policy values is permitted only when the Registry migration version is provably unchanged from the pre-commit cut. If the schema advanced, otherwise changed, or cannot be re-observed reliably, previous-binary restoration is suppressed and the release is receipted as reconciliation_required; this prevents a schema-new Registry from being restarted under a schema-old Runtime. The new service must become `active`, complete modern discovery, expose the expected 23-Tool catalog including `release.apply`, `release.get`, `runtime.describe`, and `workspace.content`, and match the bound candidate identities.

Structured self-release is opt-in operator authority. Set `ORDIVON_RELEASE_SOURCE_REPO` to the canonical Runtime owner root. In a standalone checkout this is the Git top-level; in the modular monorepo it is the real `services/runtime` directory. The deployer resolves the containing Git repository internally, while the Workspace, candidate directory, manifest, and operator artifacts remain bound to the Runtime owner root. The configured required ref (default `origin/main`) is resolved by Git in the containing repository. Standalone owners retain exact-Commit authority. Nested owners use the stronger monorepo-specific conjunction `candidate Commit is an ancestor of required ref` plus `candidate Runtime owner tree equals required-ref Runtime owner tree`; this permits unrelated owner churn without permitting an unpublished, rewritten, or stale Runtime tree. Optional `ORDIVON_RELEASE_INSTALL_DIR`, `ORDIVON_RELEASE_ENV_FILE`, `ORDIVON_RELEASE_RECEIPT_ROOT`, `ORDIVON_RELEASE_REQUIRED_REF`, and `ORDIVON_RELEASE_TIMEOUT_MS` refine the installation-owned boundary. `ORDIVON_RELEASE_DRAIN_TIMEOUT_MS` is an installation-owned deployer policy for structured releases: when present, the candidate deployer uses that positive millisecond window while holding the exclusive admission fence, rather than the compatibility CLI drain value supplied by an older Runtime. Agents cannot set or override this value through `release.apply`, and the applied plan records both the effective drain duration and its policy source. The Registry database is derived from `ORDIVON_REGISTRY_ROOT`. Callers do not provide these host paths. `runtime.describe.structuredReleaseConfigured` reports whether the authority exists. `release.apply` accepts only a Workspace identity, exact Commit, exact candidate-manifest digest, expected Tool count, and durable `clientRequestId`. If the initiating connection disappears while Runtime replaces itself, do **not** send a new release request: reconnect and call `release.get` with the same `clientRequestId`. A deterministic `effect-<effectId>` receipt is the release-effect evidence; generic process exit or transport loss is not. Explicit rollback remains `ordivon-runtime-deploy rollback --receipt <receipt>` and is never selected automatically by Runtime.

### External MCP client catalog acceptance

Runtime discovery is server truth, not proof of what a remote controller can invoke. Some MCP clients maintain an approved or frozen Tool/action snapshot independently of the live server catalog. After any `toolCatalogDigest` change, every such supported client must complete its native refresh/review flow and the effective client-side Tool projection must be re-observed before that client is accepted for workflows that depend on newly added or changed Tools. A matching local deployment receipt or successful `server/discover` probe cannot be promoted into connector parity evidence.

For the current ChatGPT custom-app model, approved MCP app changes are not automatically applied: the app owner/admin refreshes the action set and reviews newly discovered actions in ChatGPT before they become effective. This is external client state, not Runtime Registry or deployment state, and Runtime must not fabricate it. When the controlling client does not expose `release.apply` and `release.get`, self-release is `HOLD_CONNECTOR_REFRESH_REQUIRED`. Do not invoke `ordivon-runtime-deploy apply` through generic `workspace.exec` as a substitute: the low-level command remains available for explicit operator maintenance, but it does not give that controller the structured `release.apply`/`release.get` effect boundary or make transport loss safe to interpret.

A drain timeout leaves both the running installed release and the environment file untouched; it does not cancel another Agent's work. The drain window is deliberately bounded: increasing it allows already-admitted long Jobs to finish naturally under the fence, but does not create a cancel-active-work override or permit new admissions during the cutover. For the one-time bootstrap from an older Runtime that does not yet participate in `admission.lock`, moving full plan revalidation after ingress stop reduces the unavoidable zero-active→stop race to the `systemctl stop` transition itself; the post-stop Registry check still fails closed and restarts the original service if a Job entered that window. After the fenced Runtime is deployed, future cutovers no longer depend on winning a plan→apply idle-window race. Successful standard-layout deployment keeps the current and immediately previous candidate build trees and removes older exact-commit candidate directories; rollback remains receipt-owned and does not depend on those build trees. A newly installed candidate may not pass through the legacy fallback. Recovery of an uncommitted replacement and explicit rollback probe modern discovery first but may use the previous service's 2025 `initialize` Session lifecycle. A failure after replacement automatically restores the receipt-local previous artifact set and, for full releases, the previous two timeout-policy keys. There is no cancel-active-work override in the normal deployment contract.

Rollback is explicit and receipt-bound:

```bash
receipt=/var/lib/ordivon/deployments/<deployment-receipt>

scripts/ordivon-runtime-deploy rollback \
  --receipt "$receipt" \
  --confirm-receipt "$receipt" \
  --install-dir /usr/local/libexec/ordivon \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --env-file /etc/ordivon/ordivon-runtime.env \
  --drain-seconds 30
```

Rollback validates the receipt-bound install directory, service, environment file, artifact set, previous digests, recorded modes, and any receipt-bound timeout-policy transition. Before any artifact replacement it resolves the Registry database from explicit `--database` or `ORDIVON_REGISTRY_ROOT`, acquires the same exclusive `admission.lock` used by forward deployment, and waits for active/held Jobs to drain naturally within `--drain-seconds`; there is no cancel-active-work escape hatch. The fence remains held through policy/artifact restoration and service probing, so an older binary cannot receive a newly admitted Job during the cutover. It preserves the displaced current artifacts inside the same receipt before restoring the previous set and restores only `ORDIVON_DEFAULT_RUNTIME_MS` / `ORDIVON_MAX_RUNTIME_MS` to their prior value or absence; unrelated environment content is not copied into the receipt or rolled back. If restoring the previous state fails, it attempts to restore the displaced current artifact/policy state and receipts both outcomes. A successful `rollback-result.json` is itself a later release-state event: `ordivon-runtime-status` verifies the restored artifact set against it instead of continuing to compare physical state with the superseded forward deployment. At apply time the deployer records `previousCommit` only when the complete pre-deployment Runtime artifact fingerprint exactly matches an earlier compatible receipted release event. A later rollback may therefore recover that exact commit; when the restored bytes predate or use a broader historical release authority, their artifact truth remains exact but revision identity may remain explicitly unknown rather than invented. Release schema v2 owns the current 12-artifact Runtime install set; schema-v1 binary-only receipts retain explicit rollback compatibility. Historical target-aware receipts from the retired broader release authority are not silently reinterpreted by the contracted deployer. Its MCP probe accepts either the modern lifecycle or the prior legacy Session lifecycle, because rollback must be able to prove a genuinely old Runtime rather than require it to implement the new protocol. Additive query indexes and the isolated Workspace Patch receipt table are maintained outside `schema_migrations`; neither changes existing Job, Attempt, or repair semantics.

### MCP probe module placement

`ordivon-runtime-deploy`, `ordivon-runtime-reclaim`, and `ordivon-runtime-capacity-acceptance` share `mcp_probe.py`; they do not embed separate protocol clients. Repository execution remains useful during development and bootstrap, but canonical production installation is the receipt-bound release artifact set above: the three consumers and `mcp_probe.py` are installed and rolled back together with the Runtime binaries. Repository-owned systemd units and provider binaries remain outside this ordinary Runtime release transaction. A manually copied executable or support module is therefore outside canonical deployment truth until a normal release brings its digest and mode under the latest receipt. Candidate deployment requires modern discovery; reclaim uses modern discovery first and falls back to legacy initialization only so that an installed previous Runtime can still release a Workspace through its own `workspace.close` contract.

The probe identifies itself as `ordivon-mcp-probe/1` instead of inheriting Python urllib's default User-Agent. This is an explicit machine-client identity, not browser impersonation: public edge policy can observe or selectively exempt it without Browser Integrity Check turning a valid MCP route into a false negative. Local bearer credentials remain separate from any Cloudflare Access token required by the public origin.

## Runtime history archival inspection

`scripts/ordivon-runtime-archive` is currently a **repository-owned read-only planning surface** for the append-oriented Runtime Registry and immutable Attempt bundles. It is deliberately not part of the stable schema-v2 installed release artifact set yet: adding an artifact to that set requires its own additive-install/rollback contract instead of weakening the current deployer's pre-install completeness check. The Python surface owns policy and report presentation only; Registry capability validation, classification, closure counts, and sample selection come from the Rust `ordivon-runtime-inspect registry-archive` projection. The inspector does not export an archive, delete hot rows, move bundles, VACUUM SQLite, or establish deletion authority. The default seven-day policy classifies only stable terminal Jobs (`succeeded`, `failed`, `timed_out`, `cancelled`) as candidates. `lost` and `orphaned` remain excluded because Runtime repair semantics can still strengthen those states; Jobs with Runtime release effects, active/held reservations, or residual supervisor ownership are also excluded. Historical Jobs whose `current_attempt_id` is null use the same latest-`attempt_number` fallback as Runtime Core rather than being misclassified as corrupt.

```bash
scripts/ordivon-runtime-archive \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --minimum-age-hours 168 \
  --pretty
```

The report consumes one Runtime-owned read-only Registry projection and exposes classification counts, the exact eligible relational-closure row counts, registered Artifact logical payload bytes, and Job plan/snapshot logical bytes. The wrapper does not open SQLite itself. Those logical-byte values are **not** physical reclaim estimates. Attempt bundles are intentionally not recursively measured by the default inspection because live admission creates transient staging directories and an unfenced tree walk is not snapshot-consistent. A future export/apply contract must revalidate the selected identities under the Registry admission fence, preserve exact replay routing and rollback boundaries, and pack cold immutable bundles into archive segments rather than merely moving their small-file directory trees.

## Workspace lifecycle and reclaim

Workspace lifecycle has separate states and release rules:

| Classification | Meaning | Automatic action |
| --- | --- | --- |
| `blocked_active` | an unresolved Job or active/held reservation exists | never |
| `blocked_dirty` | tracked, staged, deleted, or untracked state exists | never |
| `unknown` | identity, metadata, or Git health cannot be proven | never |
| `orphan_directory` | directory exists without an identity record | never automatically; exact-ID quarantine only |
| `stale_record` | open record exists but the physical Workspace is absent | old record may be archived and deleted |
| `closable` | Workspace is healthy, clean, and has no active Job | old Workspace may be released through `workspace.close` |

Inspection remains read-only:

```bash
scripts/ordivon-runtime-reclaim inspect \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --measure-bytes \
  --pretty
```

Conservative apply uses a minimum age, an exact policy confirmation, a process lock, and receipts:

```bash
scripts/ordivon-runtime-reclaim apply \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --env-file /etc/ordivon/ordivon-runtime.env \
  --receipt-root /var/lib/ordivon/runtime/reclaim-receipts \
  --lock-file /run/ordivon-runtime-reclaim.lock \
  --minimum-age-hours 168 \
  --classification stale_record \
  --classification closable \
  --confirm-policy RECLAIM_ELIGIBLE_WORKSPACES \
  --pretty
```

The default policy is seven days and includes only `stale_record` and `closable`. A `stale_record` candidate carries a digest from inspection; apply requires the record to remain a regular file with the same digest, rechecks Workspace absence and active Jobs, copies it into the receipt, and only then deletes it. `closable` Workspaces are never removed directly; the tool calls the Runtime's `workspace.close` contract with `force=false`, preserving active-Job exclusion, dirty-state refusal, rescue refs, tombstones, and idempotency.

Dirty Workspaces remain outside automatic reclaim. Use the evidence-only review first:

```bash
ordivon-runtime-lifecycle dirty-review \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --receipt-root /var/lib/ordivon/runtime/lifecycle-receipts \
  --lock-file /run/ordivon-runtime-lifecycle.lock \
  --workspace-id <workspace-id>
```

When owner review needs the Workspace bytes to become recoverable independently of the live worktree, `dirty-checkpoint` implements the previously advisory `checkpoint_or_export` step:

```bash
ordivon-runtime-lifecycle dirty-checkpoint \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --receipt-root /var/lib/ordivon/runtime/lifecycle-receipts \
  --lock-file /run/ordivon-runtime-lifecycle.lock \
  --workspace-id <workspace-id> \
  --confirm-policy CHECKPOINT_DIRTY_WORKSPACE_STATE
```

The command is a **physical recovery operation, not a semantic disposition and not a release operation**. It refuses active/held Jobs, requires the current lifecycle classification to remain `blocked_dirty`, leaves the Workspace dirty and open, and sets `automaticDeletionAllowed=false`. It writes one immutable source-repository ref under `refs/ordivon/checkpoints/<workspace>/<stateDigest>`. The bundle retains:

- original `HEAD` as the checkpoint commit parent;
- exact raw Git index serialization in `index.raw`;
- stable index/stage projections;
- a complete `worktree/` tree containing tracked working bytes plus non-ignored untracked paths;
- an `index/` tree for the staged state; v1 fails closed on unmerged indexes and in-progress Git operations rather than pretending their continuation metadata is recoverable;
- a manifest whose `truthRole` is `physical-recovery-carrier-not-semantic-standing`.

`stateDigest` identifies this Git recovery representation. It is **not** Runtime `sourceStateDigest` and must never substitute for it. The safe release sequence remains:

```text
workspace.get -> exact Runtime sourceStateDigest
-> dirty-review / owner adjudication
-> dirty-checkpoint when independent recovery is required
-> workspace.get again (checkpoint must not change Runtime state)
-> owner explicitly chooses release
-> workspace.close(force=true, expectedSourceStateDigest=<exact current Runtime digest>)
```

A checkpoint does not imply that the state is current, useful, admitted, superseded, or safe to delete. It only removes the false coupling `preserve dirty bytes == keep a live worktree forever`. Sparse-checkout, split-index, gitlink/submodule, unmerged-index, and in-progress merge/rebase/cherry-pick/revert/sequencer Workspaces fail closed until an exact recovery contract exists for those cases.

The apply command is a policy executor, not a timer. Scheduling is intentionally separate because retention age and cadence are user policy. Failed items are recorded independently and produce a partial result instead of hiding successful actions or deleting a broader set.

### Policy-driven lifecycle

The low-level reclaim command remains the only release executor. `ordivon-runtime-lifecycle` adds the installed retention policy without creating another Workspace database or querying Registry tables directly. It derives the retention basis from Workspace creation plus the Runtime-projected latest durable Job/Attempt activity and treats active or held Jobs as leases. The packaged policy defaults every Workspace identity—generated or readable—to `ephemeral` for 48 hours. Expired `ephemeral` Workspaces may be force-closed even when dirty, but only through the existing `workspace.close(force=true)` contract, so active/held Jobs and cross-Workspace Git authority still fail closed. `review` and `pinned` classes do not opt into dirty force-close; only explicit exact/prefix rules promote selected identities to those classes. Naming is therefore no longer mistaken for retention intent.

```bash
scripts/ordivon-runtime-lifecycle inspect \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --policy-file /etc/ordivon/workspace-retention.json \
  --measure-bytes --pretty

scripts/ordivon-runtime-lifecycle sweep \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --policy-file /etc/ordivon/workspace-retention.json \
  --env-file /etc/ordivon/ordivon-runtime.env \
  --receipt-root /var/lib/ordivon/runtime/lifecycle-receipts \
  --lock-file /run/ordivon-runtime-lifecycle.lock \
  --confirm-policy APPLY_WORKSPACE_RETENTION_POLICY --pretty
```

The packaged timer runs the Runtime lifecycle service daily with a randomized delay. The Workspace phase can only select policy-expired `closable` and `stale_record` entries; dirty, active, unintegrated, pinned, unknown, and orphan-directory cases remain excluded. A clean Git worktree is only a mechanical precondition for closure, not semantic evidence that its branch work survived elsewhere. `closable` therefore requires one of two canonical integration proofs: either the Workspace HEAD is reachable from the current `sourceRepo` HEAD, or every branch-exclusive non-merge commit has a `git patch-id --verbatim` equivalent on the canonical side and there are no branch-exclusive merge commits. Ordinary whitespace-insensitive patch equivalence is intentionally insufficient for automatic deletion. Missing or uncomparable Git evidence fails closed as `unknown`; unique commits or merge topology classify as `blocked_unintegrated`.

Reclaim apply also re-reads `workspace.get` immediately before deletion. The fresh `currentHeadRevision` must equal the revision classified during planning, the Workspace must still be clean, and the fresh `sourceStateDigest` is passed unchanged to `workspace.close(expectedSourceStateDigest=...)`. This makes the final removal a compare-and-swap transition rather than a time-of-check/time-of-use guess. The subordinate reclaim receipt is linked from the lifecycle receipt. The same oneshot then runs cache pruning as a separate receipt domain; Workspace retention does not become cache authority. Packaged cache pruning reads `ORDIVON_CACHE_HIGH_WATERMARK_BYTES` and `ORDIVON_CACHE_LOW_WATERMARK_BYTES` from the same Runtime operator environment used by health/status. An explicit `ordivon-runtime-cache prune` invocation may override those values with CLI watermarks; without either an environment file or explicit values, the standalone command retains its 64 GiB / 48 GiB defaults.

The `--confirm-policy` / `--confirm-quarantine` phrases on these root-operated maintenance CLIs are human/operator anti-mistake ceremony, not semantic authority. The actual protection comes from classification, exact Workspace identity, active-Job checks, locks, before/after receipts, and preserved bytes. Future Agent-facing control surfaces should express deliberate intent and affected identities structurally rather than asking an Agent to echo a magic phrase.

Repository renames can leave a healthy worktree registered in the new Git repository while its `.git` file and Runtime record still name the old path. The repair command accepts exact `sourceRepoAliases`, verifies the recorded commit in the mapped repository, runs `git worktree repair`, rechecks the exact HEAD, and updates only the record's source repository. Unrepairable recorded data may be moved atomically to a quarantine directory and replaced by a valid closed tombstone only with a second explicit confirmation; bytes are preserved rather than deleted. A true `orphan_directory` has no Runtime opening record to repair, so it is never selected in bulk: only an exact `--workspace-id` together with the explicit quarantine flags may quarantine it. Runtime first commits an identity-unknown closed tombstone (no invented `sourceRepo`/`sourceRevision`) to fence same-ID reuse, atomically moves the bytes, and repairs linked-Git worktree registration when Git evidence is available. The quarantine receipt retains the observed current Git HEAD/status as observation only, not reconstructed opening identity.

```bash
scripts/ordivon-runtime-lifecycle repair \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime \
  --policy-file /etc/ordivon/workspace-retention.json \
  --receipt-root /var/lib/ordivon/runtime/lifecycle-receipts \
  --lock-file /run/ordivon-runtime-lifecycle.lock \
  --confirm-policy REPAIR_WORKSPACE_IDENTITIES --pretty
```

### Installation hygiene

The one-time pre-release installation hygiene pass is complete and remains available through Git history and its receipts rather than as a permanent Runtime subsystem. Target commands do not inherit the Runtime service environment. `ORDIVON_EXEC_PATH` and `ORDIVON_EXEC_HOME` explicitly retain trusted root toolchains, while request `env` values remain the only per-operation overrides. The trusted-local root authority model remains unchanged.

## Shared execution caches

Runtime separates source isolation from reusable toolchain state:

```text
cache/shared/                    global trusted-local package-download caches
cache/build/<workspaceId>/       Workspace-scoped compiled build targets for both profiles
cache/build/sources/<sha256>/    legacy source-scoped build caches retained for migration/reclaim only
cache/workspaces/<workspaceId>/  Workspace generic cache and contained-local home/tooling
cache/tmp/<workspaceId>/         Workspace temporary-file backing
```

For `trusted_local`, Runtime keeps temporary bytes in the Workspace-owned `cache/tmp/<workspaceId>/` backing but presents `TMPDIR` through the fixed-length `/tmp/ordivon-t/<20hex>` symlink derived from the canonical physical Runtime store namespace plus Workspace identity. The bounded presentation prevents child tools that derive Unix-domain sockets below `TMPDIR` from inheriting arbitrary Runtime-store or Workspace-ID path length; it does not move temporary bytes into shared `/tmp`. The alias lives below a Runtime-owned mode-0700 presentation root, is disposable, verified against the exact backing, and removed by normal Workspace close and broken-Workspace quarantine. `contained_local` continues to receive the direct Workspace-private backing path.

The committed execution environment sets explicit paths for Cargo, uv, pip, npm, pnpm/Corepack, Bun, and Go. Every Workspace still owns its own physical Cargo target backing under `cache/build/<workspaceId>/cargo`. For `trusted_local`, the Runner opens that backing and presents it at the stable compiler-visible `CARGO_TARGET_DIR=/proc/self/fd/198`; concurrent Jobs use the same pathname string but distinct inherited directory descriptors and therefore distinct mutable backings. This stable presentation exists to make content-addressed compiler wrappers such as sccache insensitive to otherwise-arbitrary Workspace target paths; Runtime does not share Cargo target bytes or operate a compiler-cache service. `contained_local` keeps the direct Workspace-private target path. Package-download caches remain global in trusted-local, while contained-local keeps its tooling/package cache Workspace-scoped.

Inspect cache retention authority without mutation. The projection separates directly reclaimable candidates, idle-open Workspace build targets that require an admission-fenced eviction cut, still-protected Workspace caches, and package-manager-owned shared caches; it does not imply authority to delete every measured byte:

```bash
scripts/ordivon-runtime-cache inspect \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --runtime-store-root /var/lib/ordivon/runtime --pretty
```

The former source-cache migration path is retired. Current execution never consumes `cache/build/sources/<sha256>/`; keeping an operator that moved Workspace build targets into that hierarchy would manufacture unused state. Existing source-scoped caches are therefore legacy reconstructible bytes and are eligible for ordinary capacity reclamation even when the same source repository still has an open Workspace.

Cache reclamation is capacity-driven rather than a blind age sweep. The packaged daily lifecycle service resolves its watermarks from `ORDIVON_CACHE_HIGH_WATERMARK_BYTES` and `ORDIVON_CACHE_LOW_WATERMARK_BYTES` in `/etc/ordivon/ordivon-runtime.env`; the packaged example remains 64 GiB / 48 GiB, while an installation may deliberately choose another pair. Those watermarks bind one explicit Runtime retention metric, `path-apparent-nondirectory-bytes-count-hardlinks-v1`: every regular-file or symlink pathname contributes its apparent byte length, hardlinks count once per retained pathname, and directory inode bytes are excluded. This additive metric is used for candidate budgeting; it is not a claim about unique filesystem allocation or bytes that `df` would recover after deletion. Active or held Workspace build targets remain protected. An open but idle Workspace does not by itself make its reconstructible Cargo/build target semantic state. Effectful prune binds `--registry-root` separately from `--database`: Runtime Core owns `registryRoot/admission.lock`, so the maintenance fence must come from that explicit authority coordinate rather than being guessed from an arbitrary database pathname. The database must be the direct canonical `registryRoot/registry.sqlite3` file; symlink or hardlink aliases fail closed before a receipt or cache effect, preventing two pathnames for one SQLite database from silently producing two unrelated admission locks. Cache inspection and fenced revalidation consume Runtime Core `registry` / `registry-markers` projections rather than reconstructing Job/Attempt semantics in Python. Under retention pressure the LRU-selected candidate carries a digest of its observed Registry Job/Attempt identity into the durable prune plan. Prune then acquires the same exclusive Registry `admission.lock` used by deployment and, while new admission is fenced, rechecks active/held ownership, the Workspace record standing, and the exact planned activity digest. A new Job that was admitted and even completed while prune waited for the fence therefore invalidates the old candidate without requiring an arbitrary one-hour, six-hour, or other age threshold. Only a still-current candidate is atomically renamed out of the execution path; recursive deletion happens after releasing the admission fence. A later Job recreates the empty Workspace build directory through normal execution-environment construction. If post-detach deletion fails, the bytes remain under `cache/.prune-detached/` and are reported as an explicit `detached_eviction` residual on the next inspection rather than disappearing from ownership. Generic and temporary cache roots remain protected for every open Workspace because this change does not establish equivalent cross-Job semantics for those paths. Legacy source-scoped build caches have no current execution consumer and remain capacity-reclaimable regardless of repository-open state. Global package-manager caches are measured but not interpreted or deleted by Runtime; mature package-manager-native pruning remains their owner. Prune execution truth is separate from retention pressure: deletion failures or a still-reclaimable residual produce `status=partial` and a nonzero exit, while a cache that remains above the high watermark only because no policy-eligible bytes remain is a successful maintenance execution with `capacityDisposition=protected_residual`. Its receipt records the residual overage and zero remaining reclaimable bytes; `runtime-status --diagnose` uses the same retention metric identity for `CACHE_HIGH_WATERMARK` rather than comparing the policy with a different hardlink-deduplicated byte count.

```bash
scripts/ordivon-runtime-cache prune \
  --database /var/lib/ordivon/registry/registry.sqlite3 \
  --registry-root /var/lib/ordivon/registry \
  --runtime-store-root /var/lib/ordivon/runtime \
  --receipt-root /var/lib/ordivon/runtime/cache-receipts \
  --lock-file /run/ordivon-runtime-cache.lock \
  --high-watermark-bytes 68719476736 \
  --low-watermark-bytes 51539607552 \
  --confirm-policy PRUNE_EXECUTION_CACHES --pretty
```

## Capacity acceptance

`scripts/ordivon-runtime-capacity-acceptance` is the repeatable public-surface proof for global admission. It opens `N+1` isolated Workspaces, admits exactly `N` bounded sleep Jobs, requires the next Job to fail with `CONCURRENCY_LIMIT`, verifies exact `active`/`limit` truth plus an explicit `holdersTruncated` completeness signal, checks that the holder identities are either complete or an honest bounded subset, waits for every admitted Job to succeed, and closes every acceptance Workspace. It emits a digest-bound JSON receipt and never reads the Registry directly.

Run it from a host shell or independent systemd unit, not from a Runtime Job: a Runtime Job would itself consume one of the slots being measured.

```bash
scripts/ordivon-runtime-capacity-acceptance \
  --env-file /etc/ordivon/ordivon-runtime.env \
  --source-repo /root/projects/ordivon-runtime \
  --source-revision "$(git -C /root/projects/ordivon-runtime rev-parse HEAD)" \
  --limit 8 \
  --receipt /var/lib/ordivon/runtime/evidence/runtime-capacity-live.json \
  --pretty
```

The command resolves the same private Runtime credential source as deploy/reclaim through the shared `mcp_probe.py`; `--token-env` is retained only as an explicit legacy override and is not the production default. The command is parameterized rather than hard-coded to eight. The Runtime capacity value follows its positive `u32` representation; the holder-identity projection may remain bounded, but incompleteness is explicit through `holdersTruncated` rather than being silently presented as the full active set.

## Secret-free status

`scripts/ordivon-runtime-status` separates three read-only operator views. The default and `--health` path is the fast automation contract: it verifies the latest successful deployment receipt, the complete installed release-artifact digests and modes, systemd state, allowlisted numeric Runtime configuration, and Runtime-projected Registry/recovery consistency. The status wrapper does not query Registry tables directly; bounded health counts and dashboard Job rows come from `ordivon-runtime-inspect registry-status`. `--dashboard` adds only cheap cockpit projections: deployment/MCP identity, capacity and recovery counts, open Workspace record/physical counts, bounded active and recent Job summaries, Runner progress freshness, and output freshness. It deliberately does **not** read stdout/stderr contents, reconcile Jobs, run Git status across all Workspaces, measure storage recursively, or scan protocol history. An optional `--source-repo` compares one local checkout with the deployed commit without making source/deployment drift a production-health failure. `--diagnose` remains the deeper maintenance path and adds protocol compatibility history, Workspace Git consistency, recursive storage measurements, stale dirty Workspace counts, and lifecycle receipts. None of the modes opens the MCP endpoint or reads/emits the bearer token.

```bash
# Fast health path; default and suitable for frequent automation.
scripts/ordivon-runtime-status
scripts/ordivon-runtime-status --health --json

# Fast human cockpit; ordinary `watch` provides refresh without another state owner.
scripts/ordivon-runtime-status --dashboard \
  --source-repo "$(git rev-parse --show-toplevel)"
watch -n 1 'scripts/ordivon-runtime-status --dashboard --width 120'

# Explicit maintenance and compatibility diagnosis; this may scan large cache trees.
scripts/ordivon-runtime-status --diagnose --json
scripts/ordivon-runtime-status --diagnose --json \
  --expected-commit "$(git rev-parse HEAD)"
```

The dashboard reports elapsed, output-idle, and progress-idle time as mechanical freshness only. It does not label a silent Job `stuck`, infer semantic completion, or turn display state into Runtime truth. Job tokens use the distinguishing suffix of the durable Job ID because UUIDv7 prefixes are deliberately time-correlated and therefore poor terminal identifiers.

The JSON schema reports separate `health` and `maintenance` states. The deployment projection names the current `releaseEvent` and `releaseDisposition`; a successful explicit rollback supersedes the forward deployment for installed-artifact truth. Exit code `1` is reserved for operational health failures such as service, deployment, Registry, recovery, exact release-artifact inconsistency, or a rollback whose restored artifact set is known but whose coherent source Commit cannot be proven. Maintenance findings such as a stale dirty Workspace produce top-level `status=attention` but retain exit code `0`; automation must inspect `maintenanceAction` when maintenance policy should gate a workflow. Compatibility observations remain advisory deletion evidence: an unreadable or truncated trace, unknown rollback protocol, or incomplete observation window blocks deletion but does not create a health incident. Exit code `2` remains reserved for an invalid invocation or unreadable mandatory input.

## Real-system release acceptance

Portable CI proves source, schema, Registry, protocol, operational-script, documentation, dependency, and secret-scanning contracts. It cannot prove the production systemd/cgroup path.

The real-system gate is:

```bash
export ORDIVON_ACCEPTANCE_OUTPUT=target/acceptance/runtime-system-acceptance.json
scripts/local-acceptance run
```

This executes all ignored systemd/cgroup fixtures serially and then performs the complete public MCP journey against a temporary loopback Runtime. The optional output path receives a JSON receipt binding the tested source commit, candidate binary digests, Tool catalog digest, and every asserted journey check.

Run this path on an owner-trusted environment that satisfies the root, systemd, and cgroup v2 requirements; ordinary hosted CI is not equivalent evidence. A release that changes dispatch, Runner behavior, supervision, cancellation, authority profiles, resource controls, or recovery must retain a successful receipt for the exact candidate commit.

## Native Windows acceptance

The Windows Job Object launcher has a separate low-level real-system acceptance because ordinary Linux CI cannot exercise Win32 Job ownership:

```bash
scripts/windows-job-launcher-acceptance.py
```

That proof exercises launcher mechanics only. The Runtime acceptance boundary is the native Windows service: SCM owns daemon lifecycle, the node advertises only `windows_native`, the launcher/privileged broker are native Windows files, and WSL is not a provider or transport dependency.

For a release/cutover acceptance, preserve evidence for all of the following:

1. `OrdivonRuntimeR6Candidate` (or its promoted successor) is `Running` with automatic SCM start.
2. Windows `runtime.describe` reports a native Windows node and only the `windows_native` execution target.
3. A limited native execution succeeds and commits launcher/target identity evidence.
4. An elevated native execution succeeds only through configured, already-present elevated provider authority.
5. Exact replay does not redispatch the effect.
6. Timeout/cancel removes the Windows Job process tree and Attempt-scoped Power Request.
7. Native immutable-input execution is limited-only and the committed limited child cannot mutate or rename the protected presentation tree.
8. Stopping the WSL distribution leaves the Windows Runtime service, native cloudflared ingress, and remote `runtime.describe` available.
9. After a real Windows reboot, SCM and ingress recover without WSL assistance.

`ORDIVON_WINDOWS_WSL_DISTRIBUTION`, `WSL_INTEROP`, `\\wsl.localhost` path projection, the WSL systemd Windows carrier, and the old WSL restart watchdog/supervisor are retired. Historical destructive-WSL evidence remains useful as migration evidence, but it is not part of the current operational procedure.

See `RUNTIME_WINDOWS_R6C_ACCEPTANCE_R1.md` for the migration/acceptance ledger and `NATIVE_RUNTIME_NODES_R1.md` for the node-ownership design history.

## Contained-local acceptance

The contained profile has a root/systemd integration fixture that uses the real Runner and cgroup v2. It proves that an unmounted secret below host `/var` is invisible, network socket creation or connection is blocked, the Workspace remains writable, inherited credential variables are absent, the systemd/Runner cgroup identity remains consistent, and `terminal_evidence` reports a clean process tree with the supplied foreign reference.

```sh
cargo build -p ordivon-runtime-core --bin ordivon-runtime-runner
ORDIVON_RUN_INTEGRATION=1 \
ORDIVON_RUNNER_PATH="$CARGO_TARGET_DIR/debug/ordivon-runtime-runner" \
  cargo test -p ordivon-runtime-core \
  runtime::integration_tests::contained_local_hides_unmounted_state_blocks_egress_and_preserves_evidence \
  -- --ignored --nocapture
```

A failed namespace setup is terminal `RUNNER_START_FAILED`; contained execution does not retry as trusted-local. `ProtectControlGroups=yes` is intentional: it keeps the host cgroup path readable but immutable so Runner-start identity, cancellation, restart recovery, and recursive residual checks refer to the same supervisor object. The stronger `strict` cgroup namespace is not used because it rewrites the Runner-visible path to `/` and destroys that identity invariant.
