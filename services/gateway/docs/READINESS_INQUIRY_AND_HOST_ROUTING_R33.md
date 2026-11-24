# Gateway R33 — UNKNOWN is an investigation result, not the end of reasoning

Date: 2026-11-19. Source-only architecture and implementation note.
No installed Gateway, Host, Cloudflare or Security policy was modified.

## Goal -> reality -> change

Goal: resolve whether a routed capability is usable, while preserving what
was observed, what was contradicted, which Owner is responsible and what
evidence is still missing.

Reality: capability.describe already summarized ready/not_ready/unknown, with
legacy available and observation_error fields. This compressed independent
propositions into one scalar: local endpoint missing, Owner RPC timeout,
malformed or duplicated target inventory, contradictory booleans, partial
Linux/Windows availability, unverified authorizations, and missing actual
execution/Artifact evidence.

Change: an opt-in and protected capability.inquire tool projects the same
bounded read-only Runtime/Host observations into structured evidence and a
forward/reverse falsification plan. It never runs its proposed effects.

## Thought LEGO: forward and reverse from testable propositions

Forward: What is the goal and the minimal supported conditions for it?
Which exact Owner can attest to each condition, and through which real
read-only status query or explicitly authorized effect?

Reverse: What could falsify each condition? What alternate explanations are
still consistent with current evidence? Which test would distinguish them,
without treating timeout as evidence of physical offline status?

The resulting Logic LEGO is a set of facts, contrary facts, unobserved
predicates, possible hypotheses and next checks. Capability LEGO invokes
only the natural Owner and never creates a Gateway Job state machine, policy
engine, or durable shadow evidence database.

## Implemented source boundaries

- logic/readiness_inquiry.py: pure typed evidence assembly and strict Runtime
  target-inventory uniqueness/boolean check; no RPC or effects.
- contracts.py: ReadinessFact, ReadinessCheck, ReadinessInquiry and
  CapabilityInquiryProjection; every next check has
  execution_state=proposed_not_executed. The legacy CapabilityDescriptor API
  is unchanged.
- capabilities/discovery.py: one existing request-scoped bounded Owner
  observation; optional inquiry retained as an in-memory private model
  attribute and NOT serialized by capability.describe/search.
- service.py + mcp_server.py: capability.inquire(capability) for an exact
  existing route, not a new science/Host truth Owner.
- security/http_ingress_guard.py: no anonymous exemption added. The new
  Tool requires a verified HTTP Principal; the independent existing Host
  PDP/machine identities remain enforced.

Evidence has a subject Owner, predicate, state (supported/refuted/
unobserved/invalid/contradictory) and source. Candidate explanations are
explicitly hypotheses, not proven root causes. A proposed check carries
forward or reverse direction, expected evidence, read-only vs separately
authorized effect, and a conspicuous not-executed marker.

Illustrative cases:
1. Runtime timeout: Gateway endpoint qualification may be known, but Owner
   status is unobserved; independent RPC and connection/timeout checks remain.
2. Runtime configured=false and available=true: preserve both facts plus a
   contradiction, never convert one into a readiness positive.
3. Linux target ready, Windows status missing: retain Linux positive and
   Windows unknown separately; Artifact bytes remain unverified until real read.
4. Host status confirmed: no assumption that specific Work access or Message
   writes are authorized.
5. Release configured: installed Tool, current Principal grant and native
   release receipt are still distinct and unobserved.

The existing 41 MCP Tool schemas remain byte-for-byte identical at their
actual native SDK contract digest:
sha256:b60a50c2371ff6afd6ba0714f71f308b4d07ed19b9aaf0cb19e8b27790abd9f3

One new explicit Tool increases package version to 0.10.16, surfaceEpoch
to 16 and native surface to 42 Tools. The new contract digest is derived
from actual native SDK tools/list and stored in mcp-surface.json, not guessed.

## Host: same semantic Owner, optional independent read transport

Original:
    READ  -> host via ORDIVON_GATEWAY_HOST_URL
    WRITE -> host via ORDIVON_GATEWAY_HOST_URL

When explicitly configured:
    READ  -> host.read via ORDIVON_GATEWAY_HOST_READ_URL
                       plus ORDIVON_GATEWAY_HOST_READ_BEARER_TOKEN_FILE
    WRITE -> host via ORDIVON_GATEWAY_HOST_URL

host.read is an MCP transport alias for the SAME natural Host Owner, not
a second Host or Security Principal. If declared but unavailable or without
valid machine credentials, it fails without fallback to legacy writable Host.
A write operation always retains the original host route.

The read-only semantic selectors now have ONE canonical home in
logic/host_tool_contracts.py, used both by the Host dispatch adapter and by
security/authorization_targets.py to build the existing PDP resource request.
Security authorization decisions and their effect boundary remain in Security.

Host status discovery uses the selected read route; its inquiry separately
records local write-route qualification. A successful Host status read is not
proof of a user's Work grant or a successful write.

No endpoint URLs, credentials, systemd services, Host roles, PG grants,
Cloudflare policies or installed Gateway releases were changed by R33.

## Verification boundary

Tests independently exercise positive and negative Owner status, timeout,
malformed and contradictory booleans, duplicate targets, partial Artifact
aggregate, successful Host status without Work grant, research metadata and
Release installed/grant uncertainty, HTTP anonymous denial, and true Host
read/write routing with no silent fallback.

Proposed verification steps are NEVER described as successfully executed.
Independent external and production confirmations remain separate tasks;
new source code cannot prove installed currentness.
