# External Provider Comparison — Research qualification recipe R1

This is a **procedure** using the existing Research Tool Qualification Packet R1, not a new qualification service or semantic registry.

1. Freeze task-local consumer, problem class, exact incumbent SourceCut, upstream release, source/package hash, license and interface.
2. Identify the actual natural owner and a versioned Tool/Skill provider. Record current owner-native availability/read-back, not Catalog metadata.
3. Create a comparable fixture with equal input, environment and threat/effect boundary. Use the native domain verifier as the judge.
4. Positive controls: baseline and candidate give contract-compatible results. Counterexamples: dirty input, unavailable resource, failed dependency, permission denial, rollback or replay according to consumer risk.
5. Record each executed command, output hash, attempt/job/fixture identity, result, acceptance predicate and any missing coverage. Failures and UNKNOWN remain first-class.
6. Use profiles/research/tool-qualification/tool-qualification-packet-r1.schema.json with standing QUALIFIED_IN_SCOPE only for a fully bound Research use; otherwise HOLD with reasons.
7. If replacing incumbent, bind generic packages/composition/docs/SUCCESSOR_CONTRACT_R1.md to actual owner evidence and require a separate production readback, authorization and recovery test before retirement.

Concrete one-command bounded fixture: catalogs/capabilities/scripts/compare_worktrunk_git.py (only Git worktree read-only inventory). The experiment's own QUALIFIED_IN_SCOPE does **not** turn a Research packet HOLD into Research approval.
