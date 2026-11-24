-- Provider-independent specification, not implementation or release evidence.
-- Natural consumers: Research/Capital derived analytics and PG-owned generic
-- queue workers. Runtime Job/OS, Host Work, Harness Run and domain acceptance
-- stay with their owners. Native falsifiers: concurrent absent-key appends,
-- payload missing with a live catalog, visibility-timeout external replay.
-- Nat values abstract exact typed identities, not cryptographic verification.
namespace OrdivonDataTransportProjection

structure Key where
  producer : Nat
  product : Nat
  version : Nat
  port : Nat -- exact name and optional port version, abstracted as one identity
  event : Nat
  deriving DecidableEq, Repr

structure Row where
  key : Key
  content : Nat
  deriving DecidableEq, Repr

def rowsFor (k : Key) (rows : List Row) : List Row :=
  rows.filter (fun row => decide (row.key = k))

def UniqueKeys (rows : List Row) : Prop :=
  ∀ k, (rowsFor k rows).length ≤ 1

-- Both independent appenders checked the same snapshot. Distinct physical
-- appends do not constitute a uniqueness constraint on a business key.
theorem absent_key_append_race (base : List Row) (a b : Row)
    (hKey : b.key = a.key) :
    ¬ UniqueKeys (base ++ [a, b]) := by
  intro unique
  have h := unique a.key
  simp [rowsFor, List.filter_append, hKey] at h

-- Abstract authoritative map: an actual owner transaction must refine this
-- atomic transition with an enforced key, content match, and receipt.
abbrev Authority := Key → Option Nat

inductive Admission where
  | claimed
  | replay
  | conflict
  deriving DecidableEq, Repr

def claim (s : Authority) (row : Row) : Admission × Authority :=
  match s row.key with
  | none => (.claimed, fun k => if k = row.key then some row.content else s k)
  | some existing => (if existing = row.content then .replay else .conflict, s)

theorem claim_other_key_frame (s : Authority) (row : Row) (k : Key)
    (h : k ≠ row.key) :
    (claim s row).2 k = s k := by
  cases hOld : s row.key <;> simp [claim, hOld, h]

theorem claimed_identity_readback (s : Authority) (row : Row)
    (h : s row.key = none) :
    (claim s row).1 = .claimed ∧ (claim s row).2 row.key = some row.content := by
  simp [claim, h]

theorem same_content_replay_has_no_new_claim (s : Authority) (row : Row)
    (h : s row.key = some row.content) :
    claim s row = (.replay, s) := by simp [claim, h]

theorem different_content_replay_is_conflict (s : Authority) (row : Row)
    (old : Nat) (hOld : s row.key = some old) (hDifferent : old ≠ row.content) :
    claim s row = (.conflict, s) := by simp [claim, hOld, hDifferent]

theorem claim_then_same_content_replay (s : Authority) (row : Row)
    (h : s row.key = none) :
    claim (claim s row).2 row = (.replay, (claim s row).2) :=
  same_content_replay_has_no_new_claim _ row (claimed_identity_readback s row h).2

-- Qualification of one exact retained snapshot. Catalog and byte observations
-- are independently qualified by their owners. None = missing evidence, not
-- a proven absent payload. This is not a backup mechanism or retention grant.
structure SnapshotRef where
  product : Nat
  version : Nat
  sourceCut : Nat
  snapshot : Nat
  deriving DecidableEq, Repr

structure RecoveryObservations where
  catalog : Option SnapshotRef := none
  completePayload : Option SnapshotRef := none
  deriving Repr

def snapshotPairQualified (requested : SnapshotRef) (o : RecoveryObservations) : Prop :=
  o.catalog = some requested ∧ o.completePayload = some requested

theorem metadata_only_not_qualified (r : SnapshotRef) :
    ¬ snapshotPairQualified r { catalog := some r } := by
  simp [snapshotPairQualified]

theorem mismatched_payload_not_qualified (r other : SnapshotRef)
    (h : other ≠ r) :
    ¬ snapshotPairQualified r { catalog := some r, completePayload := some other } := by
  simp [snapshotPairQualified, h]

theorem exact_paired_observation_qualifies (r : SnapshotRef) :
    snapshotPairQualified r { catalog := some r, completePayload := some r } := by
  simp [snapshotPairQualified]

-- One fixed message, one external non-idempotent effect. No physical
-- exactly-once claim from queue delivery or ACK. Timeout is an abstract
-- visibility transition, not a wall-clock or crash model.
structure TransportState where
  leased : Bool := false
  acked : Bool := false
  effects : Nat := 0
  deriving Repr

def initial : TransportState := {}

inductive TransportStep : TransportState → TransportState → Prop where
  | receive (s : TransportState) (h1 : s.leased = false) (h2 : s.acked = false) :
      TransportStep s {s with leased := true}
  | externalEffect (s : TransportState) (h : s.leased = true) :
      TransportStep s {s with effects := s.effects + 1}
  | timeout (s : TransportState) (h : s.leased = true) :
      TransportStep s {s with leased := false}
  | acknowledge (s : TransportState) (h : s.leased = true) :
      TransportStep s {s with leased := false, acked := true}

inductive Reachable : TransportState → Prop where
  | initial : Reachable OrdivonDataTransportProjection.initial
  | step {s t : TransportState} : Reachable s → TransportStep s t → Reachable t

theorem ack_can_follow_two_external_effects :
    ∃ s, Reachable s ∧ s.acked = true ∧ s.effects = 2 := by
  let s1 : TransportState := {initial with leased := true}
  let s2 : TransportState := {s1 with effects := 1}
  let s3 : TransportState := {s2 with leased := false}
  let s4 : TransportState := {s3 with leased := true}
  let s5 : TransportState := {s4 with effects := 2}
  let s6 : TransportState := {s5 with leased := false, acked := true}
  have h1 : Reachable s1 := Reachable.step Reachable.initial
    (TransportStep.receive initial rfl rfl)
  have h2 : Reachable s2 := Reachable.step h1 (TransportStep.externalEffect s1 rfl)
  have h3 : Reachable s3 := Reachable.step h2 (TransportStep.timeout s2 rfl)
  have h4 : Reachable s4 := Reachable.step h3 (TransportStep.receive s3 rfl rfl)
  have h5 : Reachable s5 := Reachable.step h4 (TransportStep.externalEffect s4 rfl)
  have h6 : Reachable s6 := Reachable.step h5 (TransportStep.acknowledge s5 rfl)
  exact ⟨s6, h6, rfl, rfl⟩

theorem ack_without_external_effect_reachable :
    ∃ s, Reachable s ∧ s.acked = true ∧ s.effects = 0 := by
  let s1 : TransportState := {initial with leased := true}
  let s2 : TransportState := {s1 with leased := false, acked := true}
  have h1 : Reachable s1 := Reachable.step Reachable.initial
    (TransportStep.receive initial rfl rfl)
  exact ⟨s2, Reachable.step h1 (TransportStep.acknowledge s1 rfl), rfl, rfl⟩

-- Separate model for a single exact owner's effect and ACK in the SAME
-- database transaction. Atomic commit/abort and same message identity are
-- assumptions. No filesystem/network/OS effect refines this by default.
inductive AtomicStep : TransportState → TransportState → Prop where
  | receive (s : TransportState) (h1 : s.leased = false) (h2 : s.acked = false) :
      AtomicStep s {s with leased := true}
  | abort (s : TransportState) (h : s.leased = true) :
      AtomicStep s {s with leased := false}
  | commit (s : TransportState) (h1 : s.leased = true) (h2 : s.acked = false) :
      AtomicStep s {s with leased := false, acked := true, effects := s.effects + 1}

def AtomicInvariant (s : TransportState) : Prop :=
  (s.acked = true → s.effects = 1) ∧
  (s.acked = false → s.effects = 0)

theorem atomic_step_preserves {s t : TransportState}
    (h : AtomicInvariant s) (step : AtomicStep s t) : AtomicInvariant t := by
  cases step <;> simp_all [AtomicInvariant]

inductive AtomicReachable : TransportState → Prop where
  | initial : AtomicReachable OrdivonDataTransportProjection.initial
  | step {s t : TransportState} : AtomicReachable s → AtomicStep s t → AtomicReachable t

theorem atomic_reachable_invariant {s : TransportState}
    (h : AtomicReachable s) : AtomicInvariant s := by
  induction h with
  | initial => simp [AtomicInvariant, initial]
  | step _ step ih => exact atomic_step_preserves ih step

theorem atomic_ack_requires_one_effect {s : TransportState}
    (h : AtomicReachable s) (ack : s.acked = true) : s.effects = 1 :=
  (atomic_reachable_invariant h).1 ack

-- Nonvacuity: rollback and retry can reach a committed effect once.
theorem atomic_abort_then_commit_reachable :
    ∃ s, AtomicReachable s ∧ s.acked = true ∧ s.effects = 1 := by
  let s1 : TransportState := {initial with leased := true}
  let s2 : TransportState := {s1 with leased := false}
  let s3 : TransportState := {s2 with leased := true}
  let s4 : TransportState := {s3 with leased := false, acked := true, effects := 1}
  have h1 : AtomicReachable s1 := AtomicReachable.step AtomicReachable.initial
    (AtomicStep.receive initial rfl rfl)
  have h2 : AtomicReachable s2 := AtomicReachable.step h1 (AtomicStep.abort s1 rfl)
  have h3 : AtomicReachable s3 := AtomicReachable.step h2 (AtomicStep.receive s2 rfl rfl)
  have h4 : AtomicReachable s4 := AtomicReachable.step h3 (AtomicStep.commit s3 rfl rfl)
  exact ⟨s4, h4, rfl, rfl⟩

#print axioms absent_key_append_race
#print axioms claim_other_key_frame
#print axioms claimed_identity_readback
#print axioms same_content_replay_has_no_new_claim
#print axioms different_content_replay_is_conflict
#print axioms claim_then_same_content_replay
#print axioms metadata_only_not_qualified
#print axioms mismatched_payload_not_qualified
#print axioms exact_paired_observation_qualifies
#print axioms ack_can_follow_two_external_effects
#print axioms ack_without_external_effect_reachable
#print axioms atomic_ack_requires_one_effect
#print axioms atomic_abort_then_commit_reachable
end OrdivonDataTransportProjection
