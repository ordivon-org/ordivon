# Review an external LEGO candidate — Human how-to

**Goal:** Decide whether a specific Ordivon consumer should reuse, study or reject an external tool, method, Skill or repository. This is a bounded comparison, not an installer or an approval system.

**Deliverable:** HOLD / REFERENCE_ONLY / KEEP_NATIVE / ADOPT_SCOPED / REJECT, attached to the natural Owner's existing evidence. Catalog PASS checks local provenance integrity, not live adoption or scientific equivalence.

## 1. Start from a real consumer

Read the [Catalog orientation](../README.md) and [authority map](../authority-map-r1.md). Name the current consumer and one capability it needs before searching a provider.

For the existing Worktrunk pilot, see its [source evidence](../evidence/external-lego-worktrunk-20261106.json), [provider](../providers/worktrunk.md) and [real owner-consumer comparison](WORKTRUNK_REPO_CONSUMER_SHADOW_R1.md). A GitHub star count or a successful generic demo is not evidence of useful substitution.

## 2. Verify the frozen candidate's source identity

From repository root, run:

~~~sh
python3 catalogs/capabilities/scripts/check_external_lego_evidence.py catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json
python3 -m unittest discover -s catalogs/capabilities/tests -p 'test_external_lego_evolution.py'
~~~

For this frozen record, expect an empty issues array and a passing native test suite. The checker verifies that every declared consumer path, recorded Git Blob SHA and exact SourceCut agree. It does not verify today's upstream binary, an installed service or effect authorization.

If the SourceCut cannot be obtained, inspect its exact trusted revision; do not silently replace the recorded commit with current HEAD. Separate upstream release/license verification from this local check. Treat missing evidence as HOLD.

## 3. Compare the same owner consumer, including a false case

Review the [Worktrunk native Git comparison](WORKTRUNK_REPO_CONSUMER_SHADOW_R1.md). Its fixture demonstrates read-only inventory parity, forged-path rejection, lack of proven prunable-worktree equivalence, and native rollback. Only run the documented experiment with an independently checked Worktrunk binary. Runtime continues to own Workspace/Job recovery, effects and closure.

For another candidate, qualify the real Owner's input/output, pre/postconditions, reversibility and exact consumer source. Use that Owner's native tests, appropriate formal checks and installed readback, not a new Catalog gate.

## 4. Make the smallest owner-local change or abstain

Record the exact candidate revision, licensed source, consumer, positive and negative evidence, independent verifier, installed-currentness and unresolved facts in the existing Owner Work/source. Prefer removing an obsolete wrapper, reusing a mature provider or a thin contract-bound adapter over adding another system. Only claim substitution and removed custom code after the real consumer has switched and passed Owner verification and readback.

**Current Worktrunk result:** KEEP_NATIVE; zero verified production substitutions and zero verified retired custom LOC. Further lifecycle/negative-case equivalence must precede any promotion.

Related methods: [information hiding](https://doi.org/10.1145/361598.361623), [Diátaxis](https://diataxis.fr/), [Agent Skills](https://agentskills.io/specification) and [OpenSSF Scorecard](https://openssf.org/projects/scorecard/) as a risk input, never a replacement decision oracle.
