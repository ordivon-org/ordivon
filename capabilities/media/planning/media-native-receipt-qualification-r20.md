# R20 native receipt qualification
Host #33285, follows R19 #33274 actual bound TTML execution.
Thought: in-toto material/product identity, SLSA consumer verification,
Representation-first, natural owner, UNKNOWN distinct from failure.
Logic: selected plan -> independently observed exit and receipt digest ->
strict object -> input/profile/attempt binding -> fixed raw carrier hashes ->
assertion consistency -> scoped result. Capability: existing strict_json,
assets.hash_file, native adapters, Studio Agent Surface.
I selected plan/input/closure + caller-observed receipt SHA256 and exit;
O QUALIFIED mechanicalOk true/false or UNKNOWN, inconsistent evidence rejected;
S no persistent state; pre caller-selected source closure and input binding;
post exact receipt/profile/assertions/raw carrier identity and internally
consistent verdict/exit; inv missing evidence never becomes success, exit2
cannot mean mechanical success, duplicate fields rejected; eff read-only;
c O(sum retained evidence bytes), no rerun; epsilon no independent signature,
Runtime witness or re-evaluation of native assertions, no cross-file atomic
snapshot, no semantic/publication inference; prov four real native positive
adapters + real AV negative, stale attempt, wrong identity, malformed receipt,
modified/missing raw; unfold select->decode->match->qualify.
Caller must supply independently observed receipt digest and exact plan,
not reconstruct trust from the untrusted evidence directory. This is local
readback, not an attestation authority. Native exit 2 is coherent negative.
Source closure is selected but not independently witnessed at execution.
References https://in-toto.io/docs/specs/
https://slsa.dev/spec/v1.0-rc2/verifying-artifacts
