# Engineering delivery: scoped adoption of Matt Skills, ECC and Superpowers

Use when a real consumer requests consequential source, infrastructure or domain-capability change and the next uncertainty is how to turn the goal into a verified implementation. This is a **reference for existing method-router**, not a new agent, LEGO registry, task workflow authority, universal gate or mandatory ceremony.

## Primary decision: choose the smallest useful path

- **Tiny local change with an obvious consumer:** use native Owner tools and one focused regression check. Skip spec/ticket ceremony.
- **Bounded consequential code change:** borrow Matt's to-spec → implement/TDD → two-axis code-review and Superpowers' verification-before-completion. Use Ordivon's existing worktree, Git, test and Owner interfaces.
- **Multiple independent pieces / long engineering program:** borrow Matt's to-tickets blocking graph and Superpowers' writing-plans. Record vertical, independently verifiable slices in the current Host Work/Git issue or the actual spec, rather than inventing a project engine.
- **Debugging failure:** borrow Superpowers' systematic-debugging and Matt's diagnosing-bugs; start from a reproducer, not speculation.
- **Large context or unfamiliar provider:** borrow ECC iterative-retrieval; read live tool/Owner schemas only for the selected responsibility, not a global cloned inventory.
- **Verification before claiming completion:** borrow ECC verification-loop's build/lint/test/diff intent, replacing its generic commands with the selected Ordivon Owner's mise tasks; compare against external consumer acceptance separately.

## The immutable decision boundary

Consumer/owner declares (goal identity, goal digest, relevant source revision, required outcome). Agent chooses candidate implementation and tool; the Agent cannot independently downgrade the acceptance target. Existing Composition cognitive-circuit objectiveRef and manifestDigest bind mechanical gate results to that exact declared manifest. If goal requirements change, this is a new objective revision, not a replay of old SATISFIED evidence.

For an independently declared LEGO, use all typed R2.1 coordinates from ../../recursive-lego-calculus/SKILL.md, and preserve independent proof/readback. A method Skill invocation is not a new LEGO or authorization.

## Implementation discipline (only when it affects the outcome)

1. State the final consumer, source cut, actual producer/Owner and completion predicate.
2. Find mature/native implementations first; delete obsolete responsibility rather than designing an adapter for an imagined future.
3. For consequential work, specify the minimal test seam, expected failing behavior and precise verification commands. A ticket carries blockers and one runnable vertical outcome.
4. Use an isolated Git/Runtime workspace, exact source revision and the Owner's native API; TDD at a real code seam, not forced artificial tests for prose.
5. Inspect observed output, not exit status or the model's narration alone. Separate source, merged, installed, executed and consumed truth.
6. Review against (a) the goal/spec and (b) actual code quality/Owner boundaries. Fix evidence-backed findings, then retire superseded code.
7. If an action is genuinely blocked, report the exact missing input and next executable repair; do not automatically turn caution into an indefinite planning stage.

## Do not import upstream control surfaces

Do NOT install ECC global hooks, an installer, tracker, memory layer, orchestration daemon, generic security scripts or unscoped permissions merely to follow this guidance. Foreign Skill text has no effect authority. If actual installation is later justified by a named consumer, invoke the existing skill-supply-chain-audit first and bind exact revision/bytes. Do not adopt the upstream default npm commands or coverage percentages as Ordivon-wide acceptance.

## Existing verified mechanical owner seam

- packages/composition/src/ordivon_composition/cognitive_circuit_r1.py
- packages/composition/src/ordivon_composition/verification_obligation_r1.py
- packages/composition/tests/test_cognitive_circuit_r1.py
- packages/composition/formal/Lego21OwnerBoundary.tla
- tools/repo/affected_owners.py
- AGENTS.md
- docs/architecture/AGENT_DELIVERY_CONTRACT_SPEC_R1.md

These distinguish bounded mechanical verification from domain acceptance. They do not prove the model's intent, target audience comprehension or the entire deployed system.

## Upstream sources (2026-11-09 pinned)

- Matt Pocock Skills: https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering
- ECC: https://github.com/affaan-m/ECC/tree/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b/skills
- Superpowers: https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7/skills

The procedures here are paraphrased, selected and adapted to Ordivon's native tools; upstream repositories are not vendored.
