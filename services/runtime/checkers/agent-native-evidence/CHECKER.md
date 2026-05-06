---
gate_id: agent_native_evidence
display_name: Agent-Native Evidence Boundary
layer: L10E
hardness: escalation
profiles: [full]
side_effects: false
timeout: 120
purpose: Validate read-only agent-native evidence surfaces for skills, memory/content, harness traces, and MCP-like manifests
protects_against: Skill permission laundering, stale memory as current truth, checkpoint approval laundering, token passthrough, audience/resource confusion, tool availability as authorization
---

# Agent-Native Evidence Boundary Checker

This checker validates the Phase 4 agent-native evidence import surfaces in
shadow-first mode. It is read-only and does not run agents, call tools, start
servers, refresh tokens, or approve external action.

It checks:

- skill capability is not treated as permission.
- credential-seeking skill language is caught.
- stale or cross-project memory is not cited as current authority.
- DEGRADED/BLOCKED evidence is not rewritten as a clean fact.
- checkpoints, traces, and receipts do not claim approval or truth.
- MCP-like token/resource/audience language does not collapse availability
  into authorization.

The checker does not authorize merge, release, deployment, publication,
trading, policy activation, adapter release, SDK compatibility, or external
action.
