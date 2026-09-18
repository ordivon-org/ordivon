---
name: lego-information-flow
description: "Apply information-flow and noninterference reasoning to a LEGO system when sensitive, trusted, untrusted, private, or authority-relevant information crosses components. Trace sources, transformations, stores, observers, sinks, declassification/release points, and prohibited influence. Use for credentials, prompts/context, logs, artifacts, telemetry, model/tool boundaries, multi-tenant systems, and security/privacy review. Do not confuse data visibility with execution authority or claim side-channel freedom without a formal model."
compatibility: Cross-platform. Produces information-flow/security analysis evidence; it is not a complete formal noninterference proof.
metadata:
  source-authority: information-flow security / noninterference
  lego-theory-layer: docs/LEGO_THEORY_LAYER_R1.md
  wave: "2"
---

# LEGO Information Flow Lens

Use this lens when the architecture question is "what information can influence or be observed where?"

## Procedure

1. Define the protected information and the observer/adversary model.
2. Identify information sources:
   - secrets/credentials;
   - private data;
   - untrusted webpage/input content;
   - privileged internal state;
   - provenance/evidence metadata.
3. Identify transformations, stores, channels, caches, logs, prompts, artifacts, and sinks.
4. Label flows using project-native classes; simple examples are SECRET/PUBLIC or TRUSTED/UNTRUSTED, but do not impose a universal lattice.
5. Separate:
   - information flow;
   - control flow;
   - authority/delegation;
   - physical effect.
6. Mark intentional declassification/release points and who owns that decision.
7. Apply a noninterference-style question:
   - if protected/high input changes while permitted low/public inputs remain fixed, can an unauthorized observer's visible output change?
8. Inspect implicit flows:
   - branching/control decisions;
   - error messages;
   - timing/cadence;
   - identifiers/digests/metadata;
   - retries and side effects.
9. Check persistent traces:
   - database rows;
   - logs;
   - repr/debug output;
   - crash reports;
   - telemetry;
   - artifacts;
   - model context.
10. Define negative tests that prove sensitive material is absent from prohibited sinks, while preserving evidence that allowed release occurred.

## Output

Produce:
- information-source inventory;
- observer/sink model;
- allowed/prohibited flow graph;
- declassification points;
- implicit-flow and persistence risks;
- negative leakage tests;
- unresolved side-channel assumptions.

## Promotion law

Promote only stable information-boundary, redaction, declassification, or storage/telemetry constraints that belong to the architecture and have a testable enforcement point.

## Non-claims

- Confidentiality does not imply integrity or authorization.
- No visible secret in one log does not prove noninterference.
- Data-flow diagrams do not prove absence of timing, resource, or covert channels.
- Information access does not equal permission to perform an effect.
- Cryptographic hashes may still carry sensitive linkage/provenance information depending on context.

## Stop condition

Stop when protected sources, permitted releases, prohibited sinks, and enforcement/tests are explicit enough to resolve the current design question.

Canonical external foundation:
- Information-flow security and Goguen-Meseguer-style noninterference; Cornell systems-security treatment.

Canonical local reference:
- docs/LEGO_THEORY_LAYER_R1.md
- docs/LEGO_THEORY_WAVE2_R1.md
