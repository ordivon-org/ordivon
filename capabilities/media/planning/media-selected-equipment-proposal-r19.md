# R19 Selected equipment proposal identity
Host #33213, extends #33174. RED two valid Workstation bindings A then B,
one proposal discovered A, compiled B, ready=true.
Thought: immutable selected value, dependency composition, natural owner.
Logic: physical selection -> call-local observed binding -> compile exact
selected binding -> postcondition qualification. Capability: existing owner
CLI, injected observation callback and existing compiler, stable hash_file.
I world + operation intent + observed managed binding; O proposal or
blocked; S call-local observations only; pre valid owner envelope and exact
local executable; post compiler uses same admitted binding and exports
selected ID + bindingDigest + executableDigest; inv no second managed
resolver call, no fallback on changed selected binding; eff read and
version probes only; c one resolver invocation, bounded executable rehash;
epsilon not execution-time proof, not signature, no cross-process cache;
prov actual subprocess alternating valid A/B, version-phase drift, existing
native Workstation tests; unfold observe -> select -> compile -> qualify.
Preserve independent standalone compile, non-managed direct discovery,
and owner-specific postconditions. Do not expose private binding environment
in discovery inventory. Runtime may consume explicit evidence later, but
no implicit runtime admission or semantic success. Remaining direct local
paths and other providers need their own identity qualification.
References https://martinfowler.com/bliki/ValueObject.html
https://martinfowler.com/articles/dependency-composition.html
