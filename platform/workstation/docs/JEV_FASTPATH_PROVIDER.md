# Jev Ultrafast provider materialization

Workstation v2 owns only the node-local realization of the externally maintained Jev Ultrafast runtime and its pinned Browser Harness dependency. The provider is pinned to upstream commit `452c1ad2dd628008f1d5608f28158d76e49e6cc0`; upstream `uv.lock` is realized with `uv sync --frozen --no-dev`, which currently resolves `jev-ultrafast==0.1.0` and `browser-harness==0.1.13`.

The stable locator is `/opt/ordivon/external/jev-ultrafast/current`. No model credential is stored by this provider materialization. `TYPESAFE_API_KEY` and the optional text-helper credential remain consuming-provider secrets and their absence must be reported as a readiness limitation rather than bypassed.

Workstation does not decide when Jev is suitable, does not interpret `DONE` as semantic success, and does not own browser mutation retries. Harness/Agent Service may consume the exact equipment bindings and retain effect fencing, routing, and independent outcome verification.

## Windows-native execution provider

workstation/windows/jev_fastpath_provider.py owns the Windows-native realization used when Ordivon invokes Jev through Runtime's windows_native target. It pins the official uv 0.12.3 Windows asset and digest, uv-managed CPython 3.12.13, the exact Jev source commit, and the locked jev-ultrafast 0.1.0 / browser-harness 0.1.13 package pair.

The browser contract is deliberately narrow: a dedicated persistent profile under LOCALAPPDATA/Ordivon/Chrome-CDP, a fixed loopback-only CDP endpoint, and no long-lived browser or daemon requirement. The consuming Windows job launches the dedicated Chrome on demand and may retain profile state without exposing DevTools outside Windows loopback.

Windows execution also requires PYTHONUTF8=1. Jev 0.1.0 reads its bundled snapshot.js with Python's default text encoding, and UTF-8 mode avoids locale-dependent import failure without patching the upstream package.

Workstation stores no TypeSafe or text-model credential. Those remain consumer/provider secrets. Harness owns request fences, retries/reconciliation, and independent outcome witnesses; a Jev DONE is not Workstation success evidence.
