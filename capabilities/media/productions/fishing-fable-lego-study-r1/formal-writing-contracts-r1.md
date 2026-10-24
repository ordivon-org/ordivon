# Writing creation: scoped Formal-First contract and CEGAR boundary (R1)

Natural owner: Media/Studio Production + existing Media Writing profile; the story archive is the work input, not a new truth store. This file is a source document consumed by the Production manifest, not a universal proof registry.

## Problem-first representation: three *candidate* disjoint perspectives

- **World/event**: character identities, local beliefs, actions, time, outcome; distinguish event facts from narrator/player belief.
- **Discourse/text**: chapter, focalization, disclosure order and literal rendered text.
- **Reader/encounter**: reader-observed understanding, disagreement and experience (UNKNOWN until actually observed).

These are provisional distinctions, NOT "Minimum Sufficient Representation". No proof of minimality, sufficiency, complete coverage, or safe compression is claimed.

## Minimal typed domain boundary (no new runtime object)

`SourceRevision`: exact Git SHA known to the repo.
`TextCarrier`: relative path + digest of exact bytes.
`SourceStanding`: reconstructed / independently-exact / unavailable.
`ClaimStanding`: hypothesis / supported-by-local-evidence / contradicted / unknown.
`OutputState`: planned / rendered / approved / published (existing Production schema).
`ReaderEvidence`: unknown / scoped-observation, never fabricated.

Hard prohibitions:
1. `sourceStanding=reconstructed` must never be promoted to `chat-verbatim` without an exact comparison artifact (not present).
2. `outputState=rendered` must never imply reader comprehension or domain authority.
3. `claim.source.binding` must reference a declared `sourceBindings` member; other production IDs must not be duplicated.
4. A declared `blobDigest` used as evidence must equal the actual carrier bytes.
5. No temporal/currentness assertion can be made from the revision alone; provenance does not imply truth.

## Graph / contract / composition

Existing actual graph (source repository owns the left side; the right hand side is a derived projection):

`Git source revision -> Production (owner identity) -> Claims (bounded meaning) -> Exact TextCarrier -> Media Creative Index (disposable) -> future real reader observations`

- `Production -> Claims`: binding membership, unique claim IDs, valid source paths.
- `Production -> TextCarrier`: checksum match; rendered means only that text exists, not independent literary acceptance.
- `TextCarrier -> Reader`: unproven until independent reading under a specified audience/encounter, no single universal literary score.
- Reuse `models.validate_repository()`, JSON Schema Draft 2020-12, existing Media test suite, and Creative Index. No new formal runner.

## CEGAR: one concrete refinement, not an ungrounded slogan

Question: can the current abstract state `SchemaValid` establish `OriginalTextExact`?

- A0: inspect only the Production JSON shape. It accepts an output whose `blobDigest` is a syntactically valid but incorrect hash. Thus the implication `SchemaValid => OriginalTextExact` is false; the false implication is an abstraction failure, not a real original-text witness.
- Counterexample: mutate an exact `blobDigest` to another 64-digit hex string; JSON Schema alone still accepts it. This counterexample is **not** dismissed as harmless.
- Refine A1: add a carrier-byte digest equality test. This discharges only `RegisteredCarrierIdentity`, not `OriginalChatVerbatim`.
- Remaining counterexample/unknown: a correct digest of a reconstructed text cannot imply fidelity to an earlier original that was never imported as an independent source. To refine again would require original bytes and a legitimate comparison, which this investigation does not have.
- Stop: refuse to promote `OriginalChatVerbatim` without the missing independent witness.

For narrative continuity, only begin by identifying a concrete contradiction with quotations and event/actor state; use a typed graph or finite-state model *if* that counterexample cannot be resolved by reading, editing and a short targeted test. Do not add a formal apparatus in advance.

## Which "First" changes a real decision?

- Type: version, source standing and output states.
- Graph: source/claim/output/consumer paths.
- Constraint: reject invented original-source identity, invalid references and unsupported promotion.
- State machine: draft/review/approved/published and explicit evidence steps (existing enum).
- Algebra/equivalence: substitutable writing Skills only when input/output and meaning contracts match; same Skill name does not establish equivalence.
- Declarative: required reader experience independent of tool sequence.
- Abstraction: keep model boundaries explicit, refine when counterexamples show information loss.
- Causal: changes in understanding require a suitably controlled reader comparison, not a single reviewer score.
- Compression: delete redundant instructions when outcomes and constraints survive; not proof of globally shortest text.

## MSR: explicitly demoted candidate Skill, not a default foundation

Possible use: scoped simplification heuristic under explicit task family, with cost and evidence limits.

Failure modes: (i) global minimality cannot be inferred from local deletion; (ii) proof of "sufficiency" without complete future properties is unsound; (iii) a smaller abstraction can erase attacks, causes or counterexamples; (iv) proof effort can exceed useful work; (v) optimization of representation size can reduce human/Agent comprehension.

Acceptable alternative: *fit-for-purpose representation with explicit proof obligations, UNKNOWN states, independent counterexamples and cheap replacement*, without a universal "minimal" or "sufficient" claim. If a mature mathematical kernel (SMT/TLA+/finite model checking) is genuinely necessary for a bounded owner contract, bind it to exact real variables and source witness first; do not encode art quality as a pretend theorem.

## Verification standing

- Existing Media schema and owner tests: targeted execution required on this exact revision before reporting PASS.
- Actual literary quality / reader comprehension / original chat fidelity: UNKNOWN.
- Formal model of whole Ordivon writing system: NOT CLAIMED.

## R2: consumer-driven exact carrier + local Git witness (2026-10-25)

The real hard kernel is **qualified evidence**: a syntactically well-formed result must not be silently promoted to a stronger claim about bytes, historical source, literary quality, or reader reception.

Owner-native Media `production.schema.json` now optionally accepts `outputs[].sourceCarrier` only with `blobDigest`. It is not required of the ordinary transformed video, PDF, derived book chapters, or unqualified outputs.

For each selected output `o` that declares carrier `c`:

```text
SourceCarrierAccepted(o,c) =>
    c in DeclaredSources(Production)
    AND RealFileInsideOwnerRoot(c)
    AND SHA256(ReadBytes(c)) == o.blobDigest
```

This is an executable local check, not a universal mathematical proof that a story is good. For `repository == "ordivon"` and a claim binding `(revision, path)`, the owner validator additionally demands a Git commit object and a Git blob at the declared revision and path. External repositories still own their own historical proof; the local checker cannot claim to have validated those owners.

**Concrete consumers**: `fishing-fable-lego-study-r1` source markdown, `browser-perception-note` MDX, `mhs-hardware-boundary` MDX, and the exact `ordivon-book-v0-current-zh` output. The separately-derived Ordivon Book chapters deliberately do **not** acquire `sourceCarrier`; their bytes are not equal to the whole book. This counterexample prevented the unsafe blanket rule `all outputs.digest = sources.article.digest`.

**CEGAR-inspired progression** (not a claim that an automated CEGAR model checker ran):

- A0 schema-only digest shape: concrete forged digest is admitted. False `SyntaxPass => ByteIdentity`.
- A1 optional exact source relation and byte readback: forged digest, undeclared carrier or absent digest are rejected by the existing Media owner validator.
- A2 historical source binding: a new file in the current tree can be absent in a declared frozen Git revision. For explicitly local `ordivon` source bindings, absent revision or historical blob is a fail, not a skipped test.
- Remaining unknown: source availability across clone topology or post-merge squash cannot be inferred from the local worktree; a PR qualification must fetch required history, and later source re-binding may be necessary. Current `.github/workflows/ci.yml` uses `fetch-depth: 0`, but independent post-merge currentness is still required.
- Reader comprehension, story-world state consistency and actual literary quality remain UNKNOWN. Never bridge `SourceCarrierAccepted` to any such result.

**Verification observation on this candidate**: Media owner `unittest discover -s tests -q` with declared `resolve` extra ran 200 tests PASS. The first naive run without `resolve` failed to import OpenTimelineIO; reproducing with the project's documented extra made its 13 targeted tests pass, without changing dependency versions. No separate testing framework or verifier was created. A real parser/compiler returning exit zero proves only its declared predicate; the source-to-goal refinement bridge must still be justified (Recursive LEGO formal reference).

**No MSR promotion**: the World/Discourse/Reader viewpoints are useful provisional labels, neither provably minimal nor known sufficient across unfamiliar readers, hostile context or future tasks. Deletion/optimization is governed by known consumer evidence and formal requirements, not a blanket minimality claim.

Mature theoretical substrates: CEGAR (Clarke et al., CAV 2000, https://web.stanford.edu/class/cs357/cegar.pdf); W3C PROV-O (https://www.w3.org/TR/prov-o/); JSON Schema Draft 2020-12 (https://json-schema.org/draft/2020-12). They ground scoping and provenance terminology; this implementation is a narrow owner-native validation step, not an attempt to reimplement those frameworks.
