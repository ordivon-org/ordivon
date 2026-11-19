# Gateway R34: close the read-only observation loop

Date: 2026-11-19. Source implementation, not an installed Gateway claim.

## Problem

R33 introduced capability.inquire: one actual Owner status observation,
structured UNKNOWN subclaims, and proposed next checks. It could not
execute safe follow-up confirmation nor preserve a changed response from
a second read. R34 adds an explicit optional verifyReadOnly boolean to
the same tool, default false.

## Forward and reverse Thought LEGO

Forward: identify which exact status predicates are necessary for the
selected capability and which natural Owner can assert them.

Reverse: identify missing and contradictory evidence and conduct one
bounded status re-observation, without interpreting timeouts as proof
of process failure or physical offline status.

## Logical and Capability LEGO

Logic/readiness_confirmation.py is a pure comparer. It preserves all
initial facts and the final inquiry, compares predicate/source/Owner
state sets, and catches changes to raw JSON witness digests even when
the legacy readiness projection is unchanged.

Capabilities/discovery.py performs the actual status read. Calling
capability.inquire(capability, verifyReadOnly=true) performs a second
read-only observation for the exact selected route, using existing
native Owner clients and the same timeout. Per round there is at most
one runtime.describe per target Runtime and one host.status for Host.
Research-only route metadata never produces a fake Owner status read.
An unconfigured endpoint is reported as not executed, rather than
claimed as a natural Owner failure.

Response evidence:
- initial and latest readiness state and exact Gateway projection digests;
- full initial and latest predicate/inference records;
- raw Owner status payload SHA-256 digests and canonical byte lengths,
  never arbitrary unvalidated Owner JSON;
- exact tool/request and whether the read-only probe was attempted,
  returned a status, timed out, was invalid or skipped unconfigured;
- changed facts, and verdict: changed, stable SAME OWNER observation,
  unresolved or no qualified probe.

Two equal status reads do not certify an independent authority, a physical
Job, an Authorization grant, an Artifact, or a Host mutation. Both reads
come from the same natural Owner, not independent falsification sources.

## Actual native effect evidence remains with real Owners

- Runtime: use existing execution.resolve/execution.get with exact
  requestId/OperationRef and read the native Job/Attempt status. A timeout
  or response loss must not cause submission of a second Job.
- Artifact: existing authorized artifact.read with producing Runtime
  operationRef and artifactId, never available=true from a status call.
- Host: authorized work.get/message.get under the original Host state
  and verified identity; host.status does not grant object access.
- Release: actual installed tool/receipt and runtime.release.get; an
  enabled Runtime release flag does not prove a deployed effect.
- Research: evidence owned by actual research/domain producers, not
  Discovery metadata.
- There is no new Effect runner, PDP, retry daemon, DB or virtual Owner.

## API version and test contract

Gateway package 0.10.17, surfaceEpoch17, still 42 Tools; only the new R33
inquiry Tool gains an optional input and confirmation output. The original
41 tools keep EXACT native SDK input/output schema digest:
sha256:b60a50c2371ff6afd6ba0714f71f308b4d07ed19b9aaf0cb19e8b27790abd9f3.

Tests demonstrate status recovered after timeout, repeated unknown,
ready/ready but physical Job unobserved, ready then malformed, no
configured endpoint, two native Runtime observations in mixed Artifact,
Host read-only, native MCP SDK confirmation, exact boolean input and
opaque JSON changed but same projected readiness.

This work does not install or activate Gateway, Cloudflare, Host or
Security policy. Git SourceCut and installed version are separate facts.
