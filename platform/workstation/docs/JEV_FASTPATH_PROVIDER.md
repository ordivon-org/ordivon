# Jev Ultrafast provider materialization

Workstation v2 owns only the node-local realization of the externally maintained Jev Ultrafast runtime and its pinned Browser Harness dependency. The provider is pinned to upstream commit `452c1ad2dd628008f1d5608f28158d76e49e6cc0`; upstream `uv.lock` is realized with `uv sync --frozen --no-dev`, which currently resolves `jev-ultrafast==0.1.0` and `browser-harness==0.1.13`.

The stable locator is `/opt/ordivon/external/jev-ultrafast/current`. No model credential is stored by this provider materialization. `TYPESAFE_API_KEY` and the optional text-helper credential remain consuming-provider secrets and their absence must be reported as a readiness limitation rather than bypassed.

Workstation does not decide when Jev is suitable, does not interpret `DONE` as semantic success, and does not own browser mutation retries. Harness/Agent Service may consume the exact equipment bindings and retain effect fencing, routing, and independent outcome verification.

## Windows-native execution provider

workstation/windows/jev_fastpath_provider.py owns the Windows materialization contract. The current Windows provider pins the official uv 0.13.1 executable and SHA-256, uv-managed CPython 3.15.0, a separate `.venv-py3.15.0` environment, the exact Jev source commit and locked jev-ultrafast 0.1.0 / browser-harness 0.1.13 package pair. Older `.venv` bytes remain historical, not an acceptable current Python provider.

The `status-native` command must run under the **active Windows user** (not SYSTEM) with the approved provider source and the accompanying `jev-fastpath-provider.toml` deployed in the same directory. Invoke it using the pinned Windows Python 3.15 interpreter, for example:

```powershell
& $JevPython315 .\jev_fastpath_provider.py --contract .\jev-fastpath-provider.toml status-native
```

It checks the real Windows binaries, installed Python and package versions, exact Git revision/origin/tracked state, Chrome presence and uv executable SHA-256. A successful exit (0) means only `windowsPhysicalHealthy=true`; mismatched or missing bytes return 1. An unsupported carrier or invalid environment returns 2. The response explicitly has `receiptEvaluated=false`: the Linux-owned receipt must be independently verified by the canonical Workstation provider, and Windows physical readiness is not proof of provider credentials, network reachability, or browser semantic success. This command must **not** depend on WSL interop; running the Linux `status` command in an environment lacking `WSL_INTEROP` is not an acceptable substitute.

The separate historical Linux Ansible realization uses a pinned frozen environment and does not inherit the Windows Python 3.15 qualification. Do not promote that old interpreter to a new default without independent current-source requalification.

The browser contract is deliberately narrow: a dedicated persistent profile under LOCALAPPDATA/Ordivon/Chrome-CDP, a fixed loopback-only CDP endpoint, and no long-lived browser or daemon requirement. The consuming Windows job launches the dedicated Chrome on demand and may retain profile state without exposing DevTools outside Windows loopback.

Windows execution also requires PYTHONUTF8=1. Jev 0.1.0 reads its bundled snapshot.js with Python's default text encoding, and UTF-8 mode avoids locale-dependent import failure without patching the upstream package.

Workstation stores no TypeSafe or text-model credential. Those remain consumer/provider secrets. Harness owns request fences, retries/reconciliation, and independent outcome witnesses; a Jev DONE is not Workstation success evidence.
