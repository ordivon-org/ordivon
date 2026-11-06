# Worktrunk / native Git LEGO study R1

**Capability**: Worktrunk v0.81.0 lists branches, paths, and dirty state for existing Git worktrees. Read-only inventory tested; worktree creation, execution hooks, merge and removal not qualified.

**Method**: treat branch-centric presentation as a projection of native Git authority. A better developer UX is not permission to transfer Runtime's workspace identity, source-cut, recovery or effect authority.

**Observed**: in a disposable two-worktree Git repository, Worktrunk JSON inventory matched native Git worktree path/branch inventory. Dirty file was detected; normal Git removal failed, as expected; native clean removal and readback succeeded. Worktrunk's branch_mismatch may be true for arbitrary Git-created paths. No production substitution.

**Formal standing**: incomplete candidate. An R2.1 declared LEGO needs 11 typed coordinates and a verifier-owned acceptance contract. Current evidence supports only an experiment, not all lifecycle refinement conditions.

**Verdict**: KEEP_NATIVE_GIT; investigate Worktrunk only as optional Workstation UX, not as replacement for Runtime's durable Workspace owner.

Sources and experiment: catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json and catalogs/capabilities/evidence/worktrunk-git-comparison-20261106.json.
