# Gateway Capability Authorization Contract v1

Security owns this narrow contract between a trusted ingress identity projection and the
existing Agent Admission contract.

It does not authenticate the caller, resolve or persist Grants, route a capability, execute
an effect, or establish owner/domain truth.

Input contains:

- `verifiedIngress.principalId` and `verifiedIngress.issuer`, supplied only by a trusted
  ingress verifier such as Gateway's Cloudflare Access middleware;
- `requestedCapability`, the stable Gateway capability selected by server-side routing
  semantics rather than a caller-authored identity field;
- `agentAdmission`, the existing normalized Security Agent Admission input whose Principal,
  Agent, Grant and Effect evidence must already have been established by trusted adapters.

The contract fail-closes unless the verified ingress Principal equals the Agent Admission
Principal and the requested capability equals `agentAdmission.effect.action`. It then
delegates policy evaluation to `agent-admission-v1`.

The R1 qualification target is `artifact.runtime`. This proves the seam only. It does not
authorize every Gateway capability and does not make Gateway a policy owner.

The output preserves ALLOW / STEP_UP / DENY from Security and explicitly states that an
authorization decision is not physical-effect or semantic-success evidence.
