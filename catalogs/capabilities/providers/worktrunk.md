# Worktrunk provider candidate

Status: **SCOPED READ-ONLY INVENTORY EXPERIMENT / NOT INSTALLED IN RUNTIME**.

Official repository: https://github.com/max-sixty/worktrunk

Observed upstream HEAD 181f17a7942b8e944f9c03c0f81b70e95a3b1a9b on 2026-11-06.
Reviewed release v0.81.0; archive SHA-256 and experiment binary SHA-256 are in the evidence records.
License: MIT OR Apache-2.0 verified from upstream LICENSE. GitHub REST metadata returned NOASSERTION.

Worktrunk's branch-centric presentation can improve developer ergonomics. Worktrunk's hooks, merge and removal behavior must not be conflated with the read-only inventory operation.

Runtime uses native Git worktrees under exact source, authority, execution and recovery contracts. A disposable fixture showed inventory agreement, dirty-state detection, and native Git refusal to remove dirty worktrees. This is not Runtime lifecycle or source-fencing equivalence.

Evidence: catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json
Research: catalogs/knowledge/lessons/worktrunk-workspace-native-git-r1.md
Experiment: catalogs/capabilities/evidence/worktrunk-git-comparison-20261106.json

Decision: keep native Git; Worktrunk may be an on-demand Workstation UX provider once a real consumer and separate currentness/authorization exist.
