# Gateway Artifact PDP — Security Owner (OpenID AuthZEN 1.0 + OPA)

This is a narrow standards adapter over OPA/Rego, not a second Gateway
policy authority. It listens only on loopback, requires a distinct systemd
workload credential, returns the AuthZEN boolean decision and echoes the
authenticated X-Request-ID. Failures use HTTP 4xx/503 and are rejected by
the existing Gateway PEP. The installed OPA executable must be digest-qualified.

Boundary: the policy grants evaluation solely for Runtime Artifact coordinate
formats and verified Gateway principals. Gateway MUST independently verify
Cloudflare/loopback ingress identity, requalify principal-scoped Runtime Job
identity before forwarding bytes, bind exact Artifact resource, enforce the
Security decision and return only the Owner's actual bytes. The PDP does NOT
certify Job ownership, Agent Grants, or business completion.

Production setup uses systemd LoadCredential for a distinct root-owned PDP
bearer secret and TLS private key. Install the exact Security source commit
under an immutable /opt/ordivon/security/gateway-authzen/releases directory,
pin interpreter/OPA binary, start the unit on loopback HTTPS, and configure the
Gateway's EXISTING AuthZEN endpoint/credential settings and a local trusted
CA bundle. Do not relax ingress security or enable a fail-open policy.

Native validation: use uv run --locked --project
platform/security/services/gateway-authzen --group dev python -m pytest
platform/security/services/gateway-authzen/tests -q, plus opa check --strict.

No live credentials or issuer-specific deployments belong in Git.
