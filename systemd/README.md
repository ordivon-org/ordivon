# systemd deployment

The unit in this directory is a deployment recipe for the read-only Agent Service canary. A checked-in unit file is not evidence that a release is installed or a service is running.

The unit expects an immutable release selected by:

`/opt/ordivon/agent-service-canary/current`

Materialize a release from an exact repository revision, keep `.python-version`, `pyproject.toml`, and `uv.lock` with that release, and create its environment with:

```bash
uv sync --locked --no-default-groups
```

Only after the release directory, source credential, and service identity exist should `current` be atomically pointed at that release and the unit installed/enabled. The unit uses systemd `LoadCredential=` to copy the token into the service credential directory; the application receives only `%d/agent-service-mcp.token` and does not own the credential store. `ExecStartPre --check` is the source-level canary qualification performed before the server starts.

Transport/runtime observability belongs to OpenTelemetry rather than the Agent Service semantic-evidence model. The unit launches the canary through OpenTelemetry zero-code instrumentation. Trace, metric, and log exporters are disabled by default; an operator may enable standard exporters through `/etc/ordivon/agent-service-otel.env` without changing Agent Service evidence semantics. The OpenTelemetry runtime packages are ordinary PEP 621 project dependencies, so there is no second deployment requirements file.

Use systemd's own tooling for the service boundary:

```bash
systemd-analyze security --offline=yes systemd/ordivon-agent-service-canary-mcp.service
systemd-analyze verify systemd/ordivon-agent-service-canary-mcp.service
```

The offline security review can run before installation. Full `verify` also checks referenced executables, so it is expected to fail while no release has been materialized.

Do not infer live deployment health, release provenance, OpenTelemetry export health, or a SLSA level from this repository recipe. Those claims require an actual installed/built subject and its own evidence.
