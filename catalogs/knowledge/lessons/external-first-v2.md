# Reusable lessons from the v2 generation

These are migration observations from multiple current v2 repositories, not a prescribed stack.

## Repeated pattern

Several v2 lines independently converged on the same rule:

1. select mature upstream standards/tools first;
2. keep provider-native state and formats authoritative where possible;
3. retain only a thin local semantic boundary needed for the real task;
4. separate mechanical execution success from domain/provider acceptance;
5. use differential/destructive acceptance before deleting historical behavior;
6. do not preserve implementation merely because tests exist;
7. keep provider/tool identity replaceable.

## Strong existing examples

- Operations v2: standards-first responsibility decomposition across Temporal/n8n/Runtime/OTel/systemd/Ansible/OpenTofu.
- Research v2: explicit non-owner list and external substitution rules.
- Network v2: composition + falsification environment rather than custom network stack.
- Artifact v2: native standards/validators and retirement of custom packaging/provenance concepts.
- Security v2: provider-native evidence formats and thin evidence binding.
- Distribution v2: provider-native readback, exact external-effect authority, ambiguity-aware reconciliation.
- Workstation v2: successful full retirement after responsibilities moved to mature owners.

This is the main reason the current migration can be incremental rather than a second clean-room rewrite of everything.
