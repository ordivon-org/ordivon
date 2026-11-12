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

## Host Actor delegation — reuse existing trusted OPA policy data

The same gateway_artifact.rego, AuthZEN HTTP endpoint, OPA process and systemd
LoadCredential policy-data file qualify Host state-changing operations,
Actor-filtered Work Engagement inbox queries, and the 16 original Host read
operations. There is no new policy daemon, Identity DB or Agent-issued
authorization API. With no
operator-provisioned Host grant the answer is DENY, even for an authenticated
Gateway machine bearer.

An authorized Security operator may add an array under the existing policy
data key ordivon.security.gateway_host_actor_grants. Each grant has:
active, principalId, issuer, actorRef, notBeforeEpochSeconds,
expiresAtEpochSeconds, allowedTools, allowedActions, exactRefs, and
namespacePrefixes. The optional bool allowUnscopedReads=true permits the
explicitly allowedTools to perform broad Host reads only; it never expands
a tool's authorization, write authority, identity grant or Actor identity.
A namespace prefix must end in a colon boundary
(such as work:project:) rather than being an unqualified substring.

The decision requires exact verified Principal, issuer, claimed Actor,
actual Owner tool, permitted resource and, for versioned Work, allowed
submit/review/etc action. For a relation the target is separately checked.
Inbox queries must be filtered to that Actor; global or foreign inbox queries
DENY. Host reads with object selectors require every provided selector to
match the delegated Actor or approved exactRef/namespacePrefix. A global
Host read (for example host.status, work.list, unfiltered message.search) is
allowed only with an explicit operator allowUnscopedReads grant and an
exact matching allowedTools entry. A request with a known mandatory selector
omitted is not silently downgraded to a broad scan. The Gateway binds the
complete read request (including revision, pagination and search filter) into
the AuthZEN object identity; Security never trusts an injected Actor claim.
This is explicit trusted policy data, never a value from an MCP Tool argument
or Host actor.declare. The original Runtime Artifact allow rule is retained.

For a principal that intentionally operates multiple Agents, Security can
optionally use a trusted, explicit role=operator grant and
delegatedActorPrefixes (for example agent:chatgpt:). The default grant
continues to bind **one exact** actorRef. Operator prefixes must each end
in a colon segment boundary, have a nonempty suffix, and are evaluated only
inside the authorized Principal/issuer/expiry/tool/resource/action fences.
The scope of namespacePrefixes, exactRefs, allowedTools and
allowUnscopedReads remains independent and mandatory. This is the
existing OPA role/attribute-based decision engine, not a second IAM.
The operator role delegates the ability to use those Actor identities; it
does **not** prove which autonomous Agent generated the request. Do not
provision the elevated role based on an MCP-supplied actorRef or a mere
observed message author. In production, bind it only to a positively
identified, trusted project-operator Principal; log/review changes and
test revocation through the installed PDP.

Production rules: grant provisioning, Principal-to-Actor delegation evidence,
scope, issue/expiry/revocation and release must be authorized and audited by
the real operator. The systemd LoadCredential source is copied at unit start;
changing the source file requires controlled credential reload and readback
before a revocation is trusted. No real grant or deployment credentials are
included here. The native OPA + Starlette HTTP tests use only disposable,
test-owned policy-data files. Installed HTTPS ALLOW/DENY, legitimate Agent
grant, and actual Host PG receipt still require separate production evidence.
