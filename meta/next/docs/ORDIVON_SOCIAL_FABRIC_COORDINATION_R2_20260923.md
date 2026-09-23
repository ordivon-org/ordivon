# Ordivon Social Fabric Coordination R2

Status: candidate implementation slice.

## Purpose

R2 extends the R1 rebuildable current-picture projection with deterministic signal lifecycle and shadow coordination. It deliberately does **not** create a new lock service, scheduler, winner selector, or EffectAuthority.

## Standard waist

The event envelope reuses the repository CloudEvents 1.0 contract: `specversion`, `id`, `source`, `type`, `subject`, `time`, `datacontenttype`, and `data`.

Thin Social Fabric extensions are:

- `ordivonscope`: self/direct/neighborhood/domain/system.
- CloudEvents documented `expirytime`: bounded signal validity. Legacy `ordivonexpiresat` is accepted only to replay historical checked-in cuts and must not be emitted by new producers.
- `ordivonrefreshes`: explicit refresh lineage preserving type/source/subject.
- `ordivonsupersedes`: explicit currentness replacement for the same subject.

Retraction is an explicit CloudEvent of type `io.ordivon.social.retract.v1`.

## LEGO slice

CloudEvents owner observations feed SF30 SemanticReceptor, SF31 ScopeModel, SF32 SignalLifecycle, SF33 DamageSignals, SF34 ModulatorySignals, then SF40 Candidate/Support/Inhibition shadow standing.

R2 intentionally stops before SF41 quorum and SF42 commitment authority.

## Candidate law

A candidate names one subject, holder reference, natural effect owner, operation and mode.

- shared + shared: no generic conflict.
- exclusive + shared: conflict.
- exclusive + exclusive: conflict.

Conflict is symmetric. Both candidates become `inhibited_shadow`. No winner is selected.

Support is recorded as evidence linkage only. Support count is not a score, rank, vote, quorum or priority.

## Lease boundary

CloudEvents `expirytime` bounds a Social Fabric signal. It is **not** an owner-native lease. Historical cuts using legacy `ordivonexpiresat` remain read-compatible; if both encodings are present the compiler fails closed rather than guessing precedence.

The current Runtime reservation contract owns global/workspace execution capacity and Attempt lifecycle. It does not own arbitrary subject-level resource exclusion. Therefore R2 does not reuse or reinterpret Runtime capacity reservations as VHD locks.

An active subject-level lease may only be added later if the natural effect owner exposes an auditable primitive for it.

## VHD destructive dogfood

The dogfood cut reconstructs the real September 23 WSL/VHD incident:

- two independent exclusive VHD compaction candidates;
- a concurrent WSLService activation candidate;
- DiskPart RPC failure as a damage signal;
- near-zero D: free space as a modulatory signal.

The correct R2 result is three pairwise subject conflicts, all three maintenance candidates inhibited in shadow, and no selected winner.
