# Governance Risk Engine

`governance/risk_engine/` owns allow/block decisions and policy-facing risk checks.

This package is for:

- governance decisions
- risk validation rules
- future approval or guard integrations

This package is not for:

- domain object persistence
- UI formatting
- route-local one-off checks

Default rule:

If the logic changes what the system is permitted to recommend, automate, or persist, it belongs here.
