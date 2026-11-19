# Gateway R35: distinguish factual changes from raw Owner drift

Date: 2026-11-19. Source and actual installed service are independent facts.

## Goal, actual counterexamples, and changes

Goal: UNKNOWN inquiry identifies the precise predicate, positive or contrary
observation, natural Owner, and executable read-only next check. Repeated reads
must never create spurious capability alarms when the Owner has changed only
unclassified metadata.

Reality, confirmed via an ACTUAL authenticated MCP Client to the installed
0.10.19 Gateway: capability.inquire(verifyReadOnly=true) successfully read
Linux, Windows, Host and Artifact readiness from natural Owners. Linux, Host,
and Artifact replies had readiness ready, zero changed represented predicates,
but raw Owner JSON hashes changed and verdict was changed_observation.
Host Work authorization was explicitly unobserved but the unresolved list
had zero questions. Different capability projections could also disagree
about whether a malformed unrelated Runtime target invalidated the inventory.

R35 Source changes, kept in pure Logic LEGO:
1. logic/readiness_confirmation.py distinguishes represented factual change
   from raw payload change. A real changed predicate/readiness remains
   changed_observation. If only raw Owner JSON changed with all second status
   replies valid, the original stable-predicate verdict is retained.
   A supported Gateway-local raw-digest-drift fact and an unresolved
   question make the unknown cause explicit. Existing before/after SHA256
   receipt digests remain available without changing the native MCP ABI.
2. logic/readiness_inquiry.py lists every missing, invalid or contradictory
   predicate not previously represented in unresolved_questions. For example
   Host status ready does not establish any particular work.get permission;
   Runtime target ready does not establish a Job's physical spawn.
3. logic/runtime_status.py is one pure Owner-contract rule for every consumer:
   Runtime schemaVersion exactly int 1; target inventory contains unique
   names, strict JSON booleans and no available=true when configured=false.
   Execution, Artifact and Inquiry share that rule. An unrelated duplicate
   or malformed target cannot silently make execution ready.
4. Preserve the distinction between invalid Runtime status envelope and
   invalid target status. Do not convert UNKNOWN to a false assertion.

## Forward and reverse thought versus proof

Forward thinking: inspect one exact versioned Runtime/Host status predicate,
then optionally make one additional bounded read-only Owner observation.

Reverse thinking: retain contrary and unobserved evidence, ask for an actual
Owner tool receipt and distinguish missing status schema, contradictory
target records and valid but insufficient status predicates.

A second Owner status response does NOT prove a Runtime process started,
an Artifact was read, a Host Work was authorized, or a release installed.
Those proofs remain on the EXISTING exact-principal-bound execution.get,
execution.resolve, artifact.read, native Runtime job.observe, Host work.get
and message.get paths. R35 creates no alternate execution or permission tool.

An opaque raw SHA256 change is marked unclassified; it is NOT diagnosed
as a timestamp or load change without inspecting actual Owner facts.

## Physical acceptance requirements

- Preserve the native MCP schemas of the original 41 tools.
- No public MCP Tool schema changes: advance package version to 0.10.20,
  but keep surfaceEpoch 17 unchanged and preserve all 42 Tool contracts.
- Full Gateway suite and independent root architecture tests must pass;
  frozen release installer compares actual SDK contracts to installed service.
- Use actual authenticated MCP HTTP to test new verdict and missing Work
  permission proof, not just source unit tests or a pretty status report.
- Check live Host read/write, Runtime discovery and anonymous MCP refusal.

All claims of installed currentness require a real service-version readback.
