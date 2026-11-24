# Agent engineering delivery: upstream-informed route (scoped)

Use for **substantial code/architecture changes with an actual consumer**, not routine edits, a read-only answer, or every Agent Run. The implementation Spec lives at `../../../../docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md` relative to this reference.

## Select mature methods, not new infrastructure

| Decision | Upstream method | Existing Ordivon carrier |
| --- | --- | --- |
| Defined goal, but implementation not yet specified | Matt `to-spec`: infer a bounded problem, solution, user-facing outcome, decisions and public test seam from established context | existing owner README, Host Work/GitHub issue and R2.1 when necessary |
| Several independent chunks | Matt `to-tickets`: small **vertical tracer bullets** with real blocking edges, not schema-only and API-only tickets | GitHub issues or Host Work; no new tracker |
| Interface boundary is uncertain | Matt `codebase-design`: deep module, narrow public seam; compare alternative responsibilities | natural Owner public contract, composition contracts and design-structure-matrix |
| Real regression is reproducible | Matt `tdd`, Superpowers `test-driven-development`: RED→GREEN via a public behavior | Owner-native tests with a previously failing consumer input |
| Repeated or consequential execution | Superpowers `using-git-worktrees`, `writing-plans`, `verification-before-completion` | Runtime Workspace, native `mise`, exact PR/CI/consumer receipt |
| Automatic enforcement is possible | ECC pre/post-tool hooks as **pattern** for early validation | existing Runtime/Gateway/Owner validation or GitHub CI; no copied hook runtime |
| Reviewing a candidate | Matt `code-review` (Spec + standards), Superpowers independent review | Git diff from known SourceCut, Owner tests and PR/Merge Queue |

Upstream snapshots reviewed 2026-11-09: Matt `4ae2317ddb22b046e264`; ECC `d2ef2680594f9a17526a`; Superpowers `22f0b463e7a5e579904d`. See the Spec for links, scope and non-claims. These external Skills are *method references*, not execution authority or mandatory installation.

## Contract and execution separation

1. Select consumer, current source and natural Owner; ask whether the whole responsibility can be deleted or served by a mature existing provider.
2. For a **formally admitted independently replaceable LEGO**, disclose the full typed `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` from the existing `recursive-lego-calculus` Skill. Otherwise use only the needed typed Owner interface; do not create eleven records for every file.
3. Identify `pre`, `post`, `inv`, effects and errors at the real public seam. In tests, a locally successful model/Job is a distinct observation from downstream `ConsumerAcceptance`.
4. Use a real bad/real good case, test before changing production behavior, implement one vertical slice, run affected Owner verification, inspect independent receipt and review the fixed-base diff.
5. Preserve UNKNOWN and historical witnesses. A green check does not establish semantic truth beyond its explicit assumptions.
6. Commit and integrate with existing GitHub review and Merge Queue. Track MERGED vs installed and consumed separately.

## Stop / negative routes

- Small patch with known Owner and adequate existing test? **Skip this reference** and execute the native change.
- Capability already covered at its consumer seam? **Do not add another Skill, validator, workflow, proxy or Agent**.
- Upstream differs in installation model or trust? Adopt only the method; leave foreign executable Skills uninstalled pending their own owner qualification.
- Formal proof model lacks a code/consumer bridge? State `MODEL_ONLY`, not `CODE_REFINED` or `DOMAIN_ACCEPTED`.
- Task appears blocked only because a plan is missing? Don't produce repeated plans in place of qualified executable actions. Distinguish a real blocker from an Agent preference.

This route is **advisory** and can be adapted or omitted where Owner-native practice already satisfies the consumer; only native Owner code/tests/effect acceptance can enforce guarantees.
