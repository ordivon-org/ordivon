"""Policy Platform — domain models and state machine (Phase 5.2 prototype).

This package contains the Policy lifecycle domain logic as designed in
docs/architecture/policy-platform-design.md.

Key components:
  - models.py: PolicyRecord, PolicyScope, PolicyState, PolicyRisk,
    PolicyEvidenceRef, PolicyRollbackPlan, PolicyOwner
  - state_machine.py: PolicyStateMachine with transition guards

This package does NOT:
  - Connect to an ORM or database
  - Interact with RiskEngine or Pack policies
  - Create, activate, or enforce real policies
  - Modify governance behavior
"""
