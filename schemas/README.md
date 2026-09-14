# Machine-Actionable Bridge Schemas

This directory intentionally avoids inventing a new universal ontology. The first choice is always to reuse or profile mature external representations. Local schemas exist only where Ordivon needs a concrete machine-actionable bridge between mature knowledge, decisions, workflows, tools and validation. Candidate bridge records include:

- Problem / ProblemClass
- Requirement / Constraint
- KnowledgeSource / Standard / Method / Algorithm
- Capability / ToolProvider
- Decision
- Workflow
- Validator / AcceptanceCriterion
- Evidence / Result

## Accepted bridge after cross-domain proof

`standard-native-profile-projection-v1.schema.json` is admitted after real Research, Runtime/Engineering and Game dogfood. It is a **read-only interoperability projection**, not a source-of-truth or verdict ontology. It exposes exact source identities, external authority decisions, stable trace IDs, domain-owned verdict summaries and claim boundaries so enterprise tooling can inventory/audit heterogeneous domain profiles without taking over their semantics.

## Selection policy

1. Search for a mature external representation first.
2. Profile or map that representation when possible.
3. Add a local bridge schema only when execution/integration requires one.
4. Keep local fields minimal and avoid encoding one tool or one domain into the common layer.
5. Use Game, Research and Software/Engineering as integration/compatibility tests, not as the source of the underlying theory.
6. A bridge projection must not silently normalize domain verdicts, authority types, currentness semantics or claim boundaries.
