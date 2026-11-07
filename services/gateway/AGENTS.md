# Gateway Owner — Human / Agent entrypoint

## Authority
Gateway is a thin non-authoritative northbound MCP adapter. It owns public action
names, capability projection, owner routing, wire compatibility and references.
Runtime owns Job/Attempt/physical Artifact, Host owns semantic continuity,
Harness owns Agent run, Security owns admission/PDP decisions.

## Readset
1. README.md / mcp-surface.json — declared surface, not installed evidence.
2. src/ordivon_gateway/mcp_server.py / service.py — MCP and API facade.
3. routing.py / capability_catalog.py / capability_projection.py — discovery.
4. execution_* / execution_refs.py — Runtime delegation and correlation.
5. host_*_tools.py / upstream*.py — Host/Owner forwarding.
6. access_auth.py / capability_authz.py — trusted ingress and protected calls.

## Human
Pin Git revision. Compare released tool surface with live system.describe and
the installed service. Run mise run gateway:formal:verify for TLC and the Python
bounded routing checker; run mise run gateway:verify for native consumers.
Do not interpret a model-check result as deployed authorization proof.

## Agent
Follow repository skill .agents/skills/gateway-formal-routing/SKILL.md.
Keep SPECIFIED, MODEL_VERIFIED, BOUNDED_IMPLEMENTATION_CHECKED,
SOURCE_CONSUMER_TESTED and INSTALLED_VERIFIED as distinct facts;
unexecuted or unqualified stages are UNKNOWN.

## Cleanup and release
Search imports, CI, skills, releases, and live consumers before retiring a
module. The unserved SQLite external pull transport has been removed from
Gateway source in the cleanup branch; natural PG Owner state belongs to
Runtime/Host. Keep system directories and live service data intact. Use the
existing Gateway candidate install/verify/activate procedure only after
source build, locked formal checks and native consumer readback.
