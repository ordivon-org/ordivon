# Gateway Capability Authorization Contract v2

Security owns this object-bound contract between trusted ingress identity, a Gateway-derived
capability/resource target, and the existing Agent Admission contract.

Compared with v1, v2 adds `requestedResource` and requires that the already-verified Agent
Admission Effect is bound to the exact same canonical resource id. This closes the gap where a
caller could present admission evidence for one Artifact while invoking `artifact.read` for a
different Artifact.

For the R2 qualification slice the resource is a Runtime Artifact:

- `type = ordivon.runtime.artifact`;
- `id = runtime-artifact:v1:<base64url(operationRef)>.<base64url(artifactId)>`;
- properties bind the exact Gateway `operationRef`, parsed Runtime owner, native `jobId`, exact
  `artifactId`, and identity contract version.

The base64url segments use RFC 4648 URL-safe encoding without padding. This is identity encoding,
not secrecy. Security independently reconstructs and validates the id. External-pull Artifacts are
not qualified by this contract.

The contract is still Security authorization only. It does not prove provider execution, Artifact
bytes, effect occurrence, delivery, or semantic/domain success. It is intended to sit behind an
AuthZEN-compatible PDP/adapter waist; Gateway remains the PEP and must not own Grant state.
