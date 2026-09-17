# Jev Ultrafast provider materialization

Workstation v2 owns only the node-local realization of the externally maintained Jev Ultrafast runtime and its pinned Browser Harness dependency. The provider is pinned to upstream commit `452c1ad2dd628008f1d5608f28158d76e49e6cc0`; upstream `uv.lock` is realized with `uv sync --frozen --no-dev`, which currently resolves `jev-ultrafast==0.1.0` and `browser-harness==0.1.13`.

The stable locator is `/opt/ordivon/external/jev-ultrafast/current`. No model credential is stored by this provider materialization. `TYPESAFE_API_KEY` and the optional text-helper credential remain consuming-provider secrets and their absence must be reported as a readiness limitation rather than bypassed.

Workstation does not decide when Jev is suitable, does not interpret `DONE` as semantic success, and does not own browser mutation retries. Harness/Agent Service may consume the exact equipment bindings and retain effect fencing, routing, and independent outcome verification.
