---
name: design-structure-matrix
description: Use Design Structure Matrix reasoning to test a decomposition by mapping pairwise dependencies/interactions, finding cycles, clusters, hubs, integrative elements, and likely misplaced module boundaries. Use when a system has many interacting nodes, repeated cross-module changes, unclear replacement seams, or suspected coupling. Do not treat clustering output as architecture authority.
compatibility: Cross-platform. Can be performed manually or with scripts when the graph is large.
metadata:
  source-authority: MIT DSM / Eppinger and Browning
---

# DSM

DSM is a diagnostic view of element interactions.

## Procedure

1. Start from evidenced project-native elements or project-native elements.
2. Choose one interaction semantics per matrix, or explicitly use a typed/multi-layer matrix.
3. Build M[i,j] only from observed or source-supported dependencies.
4. Distinguish directed dependency from mere similarity.
5. Identify:
   - cycles;
   - dense clusters;
   - high fan-in/fan-out elements;
   - bridge/integrative elements;
   - unexpectedly sparse or missing interfaces.
6. Compare structural clusters with the human decomposition.
7. For every mismatch, formulate a hypothesis:
   - merge;
   - split;
   - extract interface;
   - invert dependency;
   - retain current boundary with justification.
8. Validate the hypothesis against authority, replacement and acceptance boundaries before changing architecture.

## Optional quantitative extensions

When evidence quality permits, compute:
- in/out degree;
- strongly connected components;
- density;
- change-coupling frequency;
- weighted interaction strength.

Do not convert a numerical cluster score directly into a module decision.

## Output

Produce:
- matrix or sparse edge equivalent;
- cycle list;
- candidate clusters;
- hub/bridge list;
- decomposition mismatches;
- proposed architecture experiments.

## Promotion law

Promote only a reviewed architecture decision. The DSM itself remains derived analysis evidence.

## Stop condition

Stop when the remaining coupling is either intentional and contractually bounded, or additional matrix refinement would not change a decomposition decision.

Canonical local reference:
- catalogs/knowledge/lessons/lego-theory-foundations-r1.md
