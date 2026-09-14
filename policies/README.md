# Policies

Policies cover responsibility and authority boundaries around Agent action. They are a composition boundary, not an Ordivon-private authority theory or policy engine.

Use mature substrates according to the problem actually being solved. The current cross-disciplinary decomposition is registered in `knowledge/lessons/authority-mature-substrate-decomposition-r1.md` and includes institutional/governance theory, evidence-to-decision and structured decision methods, delegation/capability systems, ReBAC/ABAC, PAP/PDP/PEP policy architecture, current-authorization patterns, and adaptive/double-loop learning.

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
