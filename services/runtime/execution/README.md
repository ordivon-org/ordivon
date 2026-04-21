# Execution Layer

`execution/` is the umbrella layer for concrete action-taking components.

Current engineering mapping:

- `skills/` for reusable higher-level execution units
- `tools/` for atomic integrations and utility actions

This directory exists to make the layer explicit without forcing a risky file move today.

Rules:

- Intelligence decides what to do; execution actually does it.
- Governance can constrain execution, but execution does not own policy truth.
- If something talks to the outside world or performs a concrete side effect, it probably belongs here.
