# Worktrunk vs native Git — capability and method lesson R1

Question: can a mature external worktree UX provider replace an already-correct Ordivon owner implementation?

**Capability:** Worktrunk v0.81.0 read-only branch/path/dirty/detached status observation. Worktree creation, removal, merge, hooks, Git source-cut state and Runtime recovery were not qualified.

**Method:** treat external branch-centric presentation as an optional view of native Git; never transfer source authority to that presentation. Prefer provider-native direct reuse only if a real consumer gains value without durable adapter costs.

**Evidence:** catalogs/capabilities/evidence/worktrunk-candidate-20261106.json pins source, release, license and executable. catalogs/capabilities/evidence/worktrunk-repo-owner-consumer-shadow-20261106.json consolidates full actual Repo consumer replay plus one real Ordivon read-only shadow. In the disposable fixture, native Git and candidate-derived porcelain gave the same existing consumer output. Forged paths were distinguishable, and native prunable metadata caused the candidate projection to stop. In the actual Ordivon source snapshot, 145 worktree paths (107 detached) matched; no live cutover was performed.

**Verdict:** KEEP_NATIVE_GIT. Incomplete candidate, not admitted Recursive LEGO R2.1. A permanent translation wrapper would still depend on native Git for missing semantics and thus add maintenance rather than retire it. Older preliminary experiments remain recoverable from Git history, not copied as extra current records.
