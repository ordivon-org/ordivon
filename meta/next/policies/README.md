# Policies

Policies cover responsibility and authority boundaries around Agent action. They are a composition boundary, not an Ordivon-private authority theory or policy engine.

Use mature substrates according to the problem actually being solved. The current cross-disciplinary decomposition is registered in `knowledge/lessons/authority-mature-substrate-decomposition-r1.md`; `docs/AUTHORITY_SEMANTIC_EXPRESSION_R1.md` is the corresponding language/crosswalk profile. Together they map recurring Ordivon meanings onto institutional/governance theory, evidence-to-decision and structured decision methods, delegation/capability systems, ReBAC/ABAC, PAP/PDP/PEP policy architecture, current-authorization patterns, and adaptive/double-loop learning without creating a parallel Ordivon ontology.

Typical executable policy inputs may include:

- principal/delegated authority and its scope;
- action, target/resource, purpose and request context;
- current world/provider state;
- resource or capital envelope;
- temporal validity, attenuation and revocation state;
- external legal/contractual/provider constraints;
- reversibility and consequence information when the applicable decision method uses them;
- domain-native acceptance/verification requirements;
- evidence/retention requirements where they are part of the applicable assurance or external authority.

Human authorization is **not** a generic risk/consequence fallback. It is required only when the applicable authority actually depends on Human ownership/principal mandate, law/contract, consent/rights, an intentionally retained root credential boundary, or a target variable whose semantics are irreducibly Human.

Risk informs the applicable decision method; it is not itself universal permission authority. Epistemic uncertainty must not be silently converted into `DENY` or Human escalation. Missing/expired authority may deny an external effect, while scientific uncertainty may instead call for observation, experiment, Value of Information analysis, robust action or deferral.

Policies must not duplicate domain standards, external identity/access-control systems, policy languages or mature policy evaluators. Prefer provider-native IAM and mature engines such as Cedar/OPA/XACML-style PDP/PEP architectures where applicable. Ordivon should retain only task-local bindings, translations, provenance continuity and domain-specific inputs that remain after mature substitution.

## Executable research-to-policy composition

[`research-adopted-r1/`](research-adopted-r1/) is the current minimal executable reference profile for the composition edge that used to be missing. It uses the installed OPA/Rego evaluator directly. Research refs remain provenance on an explicit adopted decision; the adopted policy is administered separately; OPA performs the policy decision; current delegation/IAM standing remains independently required; enforcement stays with the domain/provider PEP. The profile intentionally proves that research standing alone cannot mint permission and that consequence/risk/epistemic uncertainty do not create a generic Human approval gate.

This profile is not a universal Ordivon schema and is not a `research_to_permission()` API. Domains should bind provider-native PAP/PDP/PEP/IAM representations directly whenever they can carry the complete semantics.
