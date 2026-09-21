# Gateway B02 — Dynamic Capability Projection Acceptance

Date: 2026-09-21
Status: ACCEPTED

Gateway capability discovery is now a rebuildable non-authoritative projection over current natural-owner observations.

## Contract

- static route declarations select which natural owner may answer;
- Runtime `runtime.describe` owns execution target/configuration/availability/context truth;
- Host `task.list` is used only as a read-only continuity reachability witness;
- Gateway derives a deterministic SHA-256 projection digest from the normalized snapshot;
- no capability database or mutable global registry exists.

Dynamic provider values such as Linux execution profiles and Windows authorities remain strings in projection data rather than Gateway schema enums.

## Verification

Gateway suite: 10/10 PASS after B02.
Live local projection:

- artifact.runtime — configured=true, available=true, node=linux-local;
- continuity.external — configured=true, available=true;
- execution.linux — configured=true, available=true, contexts=[trusted_local, contained_local], node=linux-local;
- execution.windows — configured=false, available=false because the C02 Windows remote owner binding is not configured.

Observed live projection digest:
`sha256:fb116f62c6295e5ea4d461b7a16be40aae616d7b7116ec46846e66fc04ff9b62`

The unavailable Windows result is intentional fail-closed projection behavior, not an inference that Windows Runtime itself is unavailable.
