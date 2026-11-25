---
schema_version: 1
id: runtime.quickstart
title: Runtime Quick Start
type: quickstart
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-runtime
audience:
  - user
  - builder
  - operator
updated: 2026-11-18
summary: Minimal path from a clean checkout to portable checks, real system acceptance, and receipted installation.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-runtime
related:
  - runtime.start
  - runtime.status
  - runtime.operations
  - runtime.data-privacy
---
<!-- cspell:words rustc clippy toplevel -->
# Runtime Quick Start

## Select the installed Runtime backend before operating it

**Observed 2026-11-18 (Linux node `linux-pg`):** the connected systemd service runs the PG-native `ordivon-runtime-pg` binary with a resource-aware queue (`runtime.describe.globalExecutionLimit=null`). The native Windows `windows-main-r6-candidate` is a **separate** node whose PostgreSQL Writer cutover has not been accepted. This page's `transactional-runtime`, `registry.sqlite3`, legacy `ordivon-runtime-mcp` and fixed-count deployment examples are **source/legacy installation examples**, **not instructions to replace or reconfigure the installed Linux PG service**. Inspect the exact node's `runtime.describe`, systemd/SCM `ExecStart`, active Registry backend, deployed executable digest and release receipt first; use the existing [operator guide](guides/operator-runtime.md) for backend-qualified actions. A documented or packaged lifecycle timer does not prove the installed timer is enabled; the observed Linux timer was disabled/inactive. Do not enable reclaim without original Harness/Workspace consumer release evidence.

## Goal

Use the portable path to inspect or contribute from any supported Linux development environment. Use the real-system path only on an owner-trusted machine with systemd, cgroup v2, and root authority. Use the production path when installing the long-running service.

## Prerequisites

```bash
git clone https://github.com/ordivon-org/ordivon.git
cd ordivon/services/runtime
git status --short --branch
rustc --version
python3 --version
```

The repository fixes Rust 1.99.1 through `rust-toolchain.toml`. Python operational scripts support Python 3.11 or newer.

## Steps

Follow the portable, real-system, configuration, deployment, and first-use steps below in order.

## 2. Run portable checks

```bash
cargo fmt --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-targets --all-features
cargo test -p ordivon-runtime-core --no-default-features --features transactional-runtime
cargo build -p ordivon-runtime-core --bin ordivon-runtime-inspect --features operator-tools
python3 -m unittest discover -s scripts/tests -v
python3 scripts/check_docs.py
scripts/local-acceptance check
```

These checks validate source formatting, Rust and Python behavior, migrations, Registry invariants, protocol schemas, deployment and rollback scripts, lifecycle policy, documentation ownership, local links, and the generated Tool reference. They do not execute the ignored systemd/cgroup tests.

## 3. Run real system acceptance

The complete acceptance path requires:

```bash
cat /proc/1/comm
cat /sys/fs/cgroup/cgroup.controllers
sudo -n true
```

Then run:

```bash
sudo scripts/local-acceptance run
```

The acceptance command:

1. builds the Runner and Runtime;
2. runs the ignored systemd supervisor tests serially;
3. runs the ignored transactional Runtime tests serially;
4. starts a temporary loopback MCP instance;
5. performs the public protocol journey;
6. emits a digest-bound JSON receipt when an output path is supplied by the underlying acceptance script.

Do not run this path on a machine that contains untrusted repositories or credentials you are unwilling to expose to a root-owned trusted-local execution service.

## 4. Configure the installed service

Copy and edit the example outside the repository:

```bash
sudo install -d -m 0700 /etc/ordivon
sudo install -m 0600 packaging/systemd/ordivon-runtime.env.example \
  /etc/ordivon/ordivon-runtime.env
sudo sh -c 'umask 077; head -c 48 /dev/urandom | base64 > /etc/ordivon/runtime-mcp.token'
sudo editor /etc/ordivon/ordivon-runtime.env
```

At minimum:

- keep `ORDIVON_BEARER_TOKEN_FILE` pointed at a private regular file containing at least 32 non-whitespace characters; the legacy inline `ORDIVON_BEARER_TOKEN` remains migration-only, and configuring both fails closed;
- keep `ORDIVON_BIND` on loopback;
- confirm `ORDIVON_EXEC_PATH` and `ORDIVON_EXEC_HOME` expose only intended trusted toolchains;
- configure `ORDIVON_DEFAULT_RUNTIME_MS`, `ORDIVON_MAX_RUNTIME_MS`, `ORDIVON_MAX_OUTPUT_BYTES`, reconciliation cadence/batch size, and cache limits for the exact Runtime binary being installed;
- for the legacy `ordivon-runtime-mcp` binary built by this guide, `ORDIVON_GLOBAL_MAX_CONCURRENCY` is a fixed Job-count limit: the example sets it to `16`, and omitting it defaults to `8` in `crates/ordivon-runtime-mcp/src/main.rs`. This is **not** the scheduling policy of every Runtime node. In particular, a separately installed PostgreSQL resource-aware node may report `globalExecutionLimit: null` through its own `runtime.describe`. Inspect the actual connected node and its installed release before applying a legacy example configuration; do not silently replace a dynamic-capacity installation with the legacy fixed-count profile.
- enable Cloudflare Access trust only when the loopback origin is reachable exclusively through the operator-owned authenticated tunnel.

## 5. Deploy with a receipt

Do not copy binaries manually. Build, plan, apply, and verify through the canonical deployment script:

```bash
owner=$(pwd -P)
git_root=$(git rev-parse --show-toplevel)
repo_head=$(git -C "$git_root" rev-parse HEAD)
commit=$(git -C "$owner" log -1 --format=%H "$repo_head" -- .)
candidate="$owner/target/ordivon-release-candidates/$commit/release"
manifest="$candidate/ordivon-deployment-manifest.json"
cargo=$(command -v cargo)

scripts/ordivon-runtime-deploy prepare \
  --source-repo "$git_root" \
  --commit "$commit" \
  --candidate-dir "$candidate" \
  --candidate-manifest "$manifest" \
  --cargo "$cargo"
```

Continue with the exact `plan` and `apply` commands in [`operations.md`](operations.md). The deployment receipt binds the source commit, build toolchain identity, binary digests, installed digests, protocol lifecycle, and Tool catalog digest.

## Verification

Verification combines the portable contract, the explicit real-system acceptance path, and the installed service checks below.

## 6. Verify the live service

```bash
scripts/ordivon-runtime-status --health --json
scripts/ordivon-runtime-status --dashboard \
  --source-repo "$(pwd -P)"
scripts/ordivon-runtime-status --diagnose --json \
  --expected-commit "$(git rev-parse HEAD)"
```

Health answers whether the current deployment is safe to operate. Dashboard is the fast human cockpit for release identity, capacity/recovery, Workspace inventory, and bounded Job freshness. Diagnose adds the slower maintenance, storage, Workspace Git, and protocol-compatibility evidence.

## 7. Use the public Tool surface

Connect an MCP client to the configured loopback or authenticated tunnel endpoint. Begin with:

```text
workspace.open
workspace.read
workspace.mutate
workspace.execPlan
job.observe
artifact.read
workspace.diff
workspace.close
```

Before calling `workspace.open`, choose and persist a unique stable `workspaceId` in the real Agent/Run; **it is required**. If the creation response is lost, call `workspace.get` with the same ID rather than creating a new Workspace. Existing Native OPENING-intent reconciliation accepts only an exact same-ID/source replay; a closed, missing, or mismatched physical carrier cannot be presumed safe from a lost Tool response.

The exact Tool names and descriptions are generated in [`reference/tools.md`](reference/tools.md). A complete executable client implementation is available in `scripts/mcp_e2e.py`.

## 8. Recover or remove

- Reconnect to existing work through `workspace.list`, `workspace.get`, `job.list`, and `job.observe`.
- For a **verified legacy SQLite-backed instance only**, observe one Workspace locally without reconciliation with `ordivon-runtime-inspect workspace --database /var/lib/ordivon/registry/registry.sqlite3 --store-root /var/lib/ordivon/runtime --workspace-id <workspace> --pretty`. This CLI path does **not** inspect a PostgreSQL Registry; for a PG instance use its native `workspace.get`, `job.get` and `job.list` projections.
- For PostgreSQL backup and recovery, use the existing pgBackRest route in [operations.md](operations.md). The `scripts/backup.py` and `scripts/restore.py` commands are legacy SQLite-only.
- Repair only through the documented doctor/repair sequence in [`recovery.md`](recovery.md).
- Release Workspaces through `workspace.close` or the receipted lifecycle tools, never by deleting directories directly.
- For instance retirement, export required state, stop the service, preserve any mandated evidence, then delete the operator-owned state roots described in [`data-and-privacy.md`](data-and-privacy.md).

## Run the bounded Runtime demonstration

The repository includes a small presentation-ready proof that targets the installed loopback service. It does not build or launch a second Runtime and it never prints the bearer token.

```bash
python3 scripts/demo_runtime_flow.py \
  --receipt /tmp/ordivon-runtime-demo.json
```

The demonstration creates a temporary Git source repository from `examples/runtime-demo`, opens an exact-revision Workspace, applies one digest-guarded synchronous `workspace.mutate`, admits a three-step `workspace.execPlan`, recreates the MCP client, replays the exact execution request, recovers the same Job through `job.list`, reads terminal evidence, reviews the structured diff, and compare-and-closes the reviewed `sourceStateDigest`.

Its terminal output is a compact projection of real Runtime responses. The receipt contains selected identities, statuses, timings and digests for media or documentation use; it excludes the bearer token, local source paths, Runtime state roots and unrelated Jobs.
