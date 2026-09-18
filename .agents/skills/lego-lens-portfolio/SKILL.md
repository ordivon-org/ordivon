---
name: lego-lens-portfolio
description: Govern the long-term Ordivon LEGO lens portfolio after Router/Compiler applications. Use to distinguish cross-cutting lenses from domain-native methods and meta-operators, reconcile repeated application evidence, prevent lens-count inflation, and recommend ADMIT / KEEP / MERGE / RETIRE / RESERVE outcomes without owning project truth.
compatibility: Cross-platform. Reads lens registry and evidence and produces derived portfolio decisions; it does not select the current problem MSTS, compile new lenses, or alter domain/project truth.
metadata:
  method-contract: docs/LEGO_LENS_PORTFOLIO_R1.md
  router-contract: docs/LEGO_LENS_ROUTER_R1.md
  compiler-contract: docs/LEGO_LENS_COMPILER_R1.md
  registry: knowledge/registries/lego-lens-registry-r1.json
  universe: docs/LEGO_LENS_UNIVERSE_R1.md
---

# LEGO Lens Portfolio

Keep the candidate theory universe open while keeping the durable active lens portfolio sparse.

## Activation

Use when:
- one analysis names many disciplines and it is unclear which are actually lenses;
- a candidate has accumulated shadow/prospective evidence;
- two registry lenses increasingly overlap;
- a recurring domain method is being mistaken for a cross-cutting lens;
- registry/context/routing cost is rising.

Do not use this operator to choose the current problem MSTS. That remains Lens Router's job.

## Three-way classification

For every method named in an analysis classify one primary role for that case:

1. LENS — reusable cross-cutting perspective over a material uncertainty; Router may select it in MSTS.
2. DOMAIN_METHOD — mature natural method owning a bounded technical question or verification step.
3. OPERATOR — meta-method framing, routing, compiling, validating, or governing analysis.

Additional case states are INFORMATIVE_ONLY, DEFERRED, and REJECTED.

A discipline may play different roles in different cases, but the role must be explicit. Do not count every invoked domain method as an active lens.

## Portfolio procedure

1. Bind exact application evidence, Router MSTS, Compiler evidence, domain handoffs, and concrete decision/test deltas.
2. Normalize every named discipline to LENS / DOMAIN_METHOD / OPERATOR / INFORMATIVE_ONLY / DEFERRED / REJECTED.
3. Apply MSTS pressure:
   - 0 lenses is valid;
   - prefer 1;
   - 2 is common for orthogonal uncertainties;
   - 3 requires explicit marginal-value justification;
   - more than 3 requires exceptional per-lens proof.
   Domain methods do not count toward the lens number.
4. Separate unique lens yield from supporting execution. A domain method may create decisive evidence without becoming a durable lens.
5. Accumulate longitudinal evidence: applications, decisions changed, hazards/boundaries exposed, tests created, invalid uses prevented, justified no-change, false leads, domain-method preemptions, and qualitative context/evidence cost.
6. Audit overlap. If two lenses repeatedly answer the same question with the same evidence and decision consequence, recommend MERGE or RETIRE.
7. Recommend ADMIT / KEEP / MERGE / RETIRE / RESERVE.
8. Preserve authority. Portfolio recommendations are derived governance only.

## Anti-inflation laws

- many invoked methods != many active lenses;
- decisive evidence != durable lens status;
- discipline prestige != admission;
- one successful case != cross-domain retention;
- repeated terminology without decision delta -> MERGE/RETIRE;
- domain-native methods remain domain methods unless repeated cross-domain evidence shows a distinct reusable routing question;
- operators never count toward MSTS.

## Pressure-test rule

When an analysis reports more than 3 ACTIVE lenses, perform a mandatory role audit.

Ask:
- Which lens owns the top-level uncertainty?
- Which methods merely implement or verify that lens?
- Which methods are natural domain owners?
- Which items produced no unique decision delta?
- Can the same result be reproduced with at most 3 cross-cutting lenses plus domain-method handoffs?

If yes, contract the active-lens set.

## Output

Produce:
- case/evidence boundary;
- original named methods;
- normalized role table;
- contracted MSTS when needed;
- unique contribution per retained lens;
- domain-method handoffs;
- rejected/deferred/informative-only methods;
- longitudinal evidence updates;
- lifecycle recommendation;
- registry mutation proposal, if any;
- stop condition.

## Promotion law

Portfolio may recommend registry changes, but mutation remains explicit and reviewable. It cannot create project truth or turn a domain method into a lens by repeated mention alone.

## Stop condition

Stop when every named method has one bounded role, MSTS pressure is satisfied, lifecycle standing is explicit, and any registry proposal is bounded.

Canonical references:
- docs/LEGO_LENS_PORTFOLIO_R1.md
- docs/LEGO_LENS_ROUTER_R1.md
- docs/LEGO_LENS_COMPILER_R1.md
- knowledge/registries/lego-lens-registry-r1.json
