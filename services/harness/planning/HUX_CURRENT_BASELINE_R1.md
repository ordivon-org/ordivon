# Harness UX Current Baseline R1

Date: 2026-09-23
Base revision: `8a5127a96272fe1d157cd636ac3b73942cb2d469`

## Frozen observations

- `services/harness` had no source diff from the prior UX audit revision
  `8778425bafbaedf9ab5f99037fb3935271d3f47c`.
- `ordivon_harness.api` exported 47 compatibility-stable symbols.
- `HarnessAgentRun.create` required ten explicit composition coordinates including
  state root, exact Run Contract, adapter factory and optional cognition/execution/Tool clocks.
- Harness had zero imports from `ordivon_composition`.
- The product-level abstractions `AgentRunBinding`, `AgentPreset`, `ToolBundle`,
  `SkillBundle`, `ConversationView` and `AgentWorkspace` did not exist.
- `docs/QUICKSTART.md` referenced the retired `ordivon-harness capabilities` command while
  the current CLI parser did not expose it.
- Existing documentation validation still passed despite that command drift.

## Boundary

This baseline records source facts only. It does not claim that a UX refactor is semantically
complete, and it does not authorize changes to Harness, Runtime, Host, Gateway or domain truth.
