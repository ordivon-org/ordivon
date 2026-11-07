---
name: compositional-contracts
description: "Apply compositional reasoning and assume-guarantee contracts to a system whose parts must compose, interoperate, or remain replaceable. Identify environmental assumptions, component guarantees, compatibility obligations, refinement/substitutability conditions, and composition failures. Use when local correctness is being promoted into a whole-system claim, interfaces are meant to be replaceable, or independently developed modules/providers must compose. Category-theoretic language is optional and may be used only when it clarifies composition laws; do not force it onto ordinary interfaces."
compatibility: Cross-platform. Produces contract/composition analysis evidence; it is not a formal verifier by itself.
metadata:
  source-authority: NASA/CMU assume-guarantee compositional verification; Fong-Spivak applied compositionality
---

# Compositional Contracts

Use this method when "each part works" is not enough to establish that the assembled system works.

## Procedure

1. Name the composition under review and its intended whole-system property.
2. Identify the components and the exact interfaces/wiring by which they compose.
3. For each component write:
   - assumptions about its environment;
   - guarantees it provides when those assumptions hold;
   - state/effect/authority it owns;
   - observations/evidence by which the guarantee can be checked.
4. Check assumption discharge:
   - which other component or environment guarantees each assumption?
   - which assumptions are merely hoped for?
5. Check compatibility at each seam:
   - protocol/version;
   - input/output shape;
   - timing/order;
   - identity;
   - authority;
   - failure/retry semantics;
   - resource or capacity bounds;
   - domain-specific invariants.
6. Check refinement/substitutability:
   - can candidate B replace A without strengthening assumptions or weakening required guarantees?
   - if not, name the broken obligation.
7. Check composition closure:
   - do local guarantees establish the desired system property?
   - are there circular assumptions with no external anchor?
8. When useful, express composition algebraically:
   - sequential/parallel composition;
   - associativity or re-wiring invariants;
   - identity/no-op component;
   - quotient/residual obligation for a missing component.
9. Use category-theoretic terms only if they reduce ambiguity in the composition law. A diagram that merely looks categorical adds no evidence.
10. Turn disputed obligations into executable contract or counterexample tests where possible.

## Output

Produce:
- composition target/property;
- component contract table;
- assumption-discharge map;
- seam compatibility obligations;
- substitutability/refinement findings;
- circular/unproved assumptions;
- candidate contract tests or counterexamples.

## Promotion law

Promote only architecture-relevant obligations that must remain true across implementations, such as a stable interface contract, replacement condition, or explicit environmental assumption.

## Formal proof and test substitution

An architecture contract is not by itself a machine-checked theorem.
When a caller proposes to remove duplicated tests or replace an Owner
module, bind the exact original consumer, SourceCut and scope of the
property. Route through the Owner's existing formal native toolchain,
not a new checker. Require distinct evidence links:

- Specification and assumptions -> faithful model and explicit bounds.
- Model -> proof/model-checking result with falsifying controls.
- Model -> actual Rust/Python/TypeScript refinement witness, not just
  similar names or a successful compilation.
- Code -> native installed/runtime consumer behavior for effects not
  captured by the proof.

A new LEGO is substitutable only if it does **not strengthen** the
consuming assumptions or **weaken** required guarantees, preserves
state/effect/provenance obligations and the R2.1 11-coordinate contract.
A test is dominated only when its exact property and fault model are
covered by the current proof **and** implementation refinement;
otherwise retain the distinct real consumer check. Missing or stale
evidence stays UNKNOWN. For physical source/Workspace retirement,
traverse every final consumer, preserve unique original bytes in a
read-back-verified native Artifact if needed, then invoke the existing
Owner's deletion primitive with source-state comparison.

Human readers: choose the desired observable outcome and decide
whether remaining physical verification is worth its cost.
Agents: resolve current SourceCut, obligations and real consumers,
run the selected native proof and verification, and record the
substitution/deletion evidence in the existing Host Work; never
register another verifier, LEGO registry or lifecycle authority.

## Non-claims

- Local correctness does not imply composed correctness unless assumptions are discharged.
- Same API shape does not imply substitutability.
- A contract document does not prove the implementation satisfies the contract.
- Category-theoretic notation does not create a formal proof unless the model and laws are actually formalized.

## Stop condition

Stop when the composition decision has explicit obligations and every material assumption is either discharged, tested, or recorded as unresolved.

Canonical external foundations:
- NASA CoCoSim / assume-guarantee compositional verification.
- CMU compositional model checking and assume-guarantee reasoning.
- Fong & Spivak, Seven Sketches in Compositionality / MIT Applied Category Theory.

Canonical local reference:
- docs/LEGO_THEORY_WAVE2_R1.md
