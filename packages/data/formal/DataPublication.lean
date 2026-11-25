-- A finite control-state specification for a Data Product's published view.
-- Data owns ONLY the abstract shared contract. The source owner, Runtime and
-- PostgreSQL must separately establish concrete implementation refinement.
namespace OrdivonDataPublication

inductive Phase where
  | candidate
  | validated
  | committed
  | published
  | retired
  | reclaimed
  deriving DecidableEq, Repr

structure Snapshot where
  phase : Phase := .candidate
  validatedEvidence : Bool := false
  commitReceipt : Bool := false
  activeReaders : Nat := 0
  retentionCleared : Bool := false
  deriving Repr

def initial : Snapshot := {}

-- Legal abstract effects; atomicity is an assumption of this control model,
-- not a claim that a PostgreSQL transaction/Artifact pointer already refines it.
inductive Step : Snapshot → Snapshot → Prop where
  | verify (s : Snapshot) (h : s.phase = .candidate) :
      Step s {s with phase := .validated, validatedEvidence := true}
  | commit (s : Snapshot) (hPhase : s.phase = .validated)
      (hEvidence : s.validatedEvidence = true) :
      Step s {s with phase := .committed, commitReceipt := true}
  | publish (s : Snapshot) (hPhase : s.phase = .committed)
      (hEvidence : s.validatedEvidence = true)
      (hReceipt : s.commitReceipt = true) :
      Step s {s with phase := .published}
  | acquire (s : Snapshot) (h : s.phase = .published) :
      Step s {s with activeReaders := s.activeReaders + 1}
  | retire (s : Snapshot) (h : s.phase = .published) :
      Step s {s with phase := .retired}
  | release (s : Snapshot) (hPhase : s.phase = .published ∨ s.phase = .retired)
      (hReaders : s.activeReaders > 0) :
      Step s {s with activeReaders := s.activeReaders - 1}
  | clearRetention (s : Snapshot) (h : s.phase = .retired) :
      Step s {s with retentionCleared := true}
  | reclaim (s : Snapshot) (hPhase : s.phase = .retired)
      (hReaders : s.activeReaders = 0)
      (hRetention : s.retentionCleared = true) :
      Step s {s with phase := .reclaimed}

def Safety (s : Snapshot) : Prop :=
  (s.phase = .published →
    s.validatedEvidence = true ∧ s.commitReceipt = true) ∧
  (s.phase = .committed →
    s.validatedEvidence = true ∧ s.commitReceipt = true) ∧
  (s.phase = .reclaimed →
    s.activeReaders = 0 ∧ s.retentionCleared = true)

theorem initial_safe : Safety initial := by
  simp [Safety, initial]

theorem step_preserves_safety {s t : Snapshot}
    (hSafe : Safety s) (hStep : Step s t) : Safety t := by
  cases hStep <;> simp_all [Safety]

inductive Reachable : Snapshot → Prop where
  | initial : Reachable OrdivonDataPublication.initial
  | step {s t : Snapshot} : Reachable s → Step s t → Reachable t

theorem all_reachable_safe {s : Snapshot}
    (h : Reachable s) : Safety s := by
  induction h with
  | initial => exact initial_safe
  | step _ hstep ih => exact step_preserves_safety ih hstep

theorem published_requires_validation_and_commit {s : Snapshot}
    (h : Reachable s) (hPublished : s.phase = .published) :
    s.validatedEvidence = true ∧ s.commitReceipt = true :=
  (all_reachable_safe h).1 hPublished

theorem reclaimed_requires_no_readers_and_retention_release {s : Snapshot}
    (h : Reachable s) (hReclaimed : s.phase = .reclaimed) :
    s.activeReaders = 0 ∧ s.retentionCleared = true :=
  (all_reachable_safe h).2.2 hReclaimed

-- Deliberate counterexample: a naive direct publication without validated
-- evidence or a commit receipt violates the inductive safety predicate.
def naivePublish (s : Snapshot) : Snapshot := {s with phase := .published}

theorem direct_publication_without_checks_is_unsafe :
    ¬ Safety (naivePublish initial) := by
  simp [Safety, naivePublish, initial]

-- Exact reclamation evidence, independent of the publication control model.
-- The generation abstracts the observation cut, not a clock or a filename.
structure ReclaimCut where
  subject : Nat
  generation : Nat
  deriving DecidableEq, Repr

structure ReclaimObservation where
  current : Option ReclaimCut := none
  noReaders : Option ReclaimCut := none
  retentionRelease : Option ReclaimCut := none
  -- No remaining preservation obligation, or a distinct exact retained copy
  -- independently satisfies every remaining obligation.
  preservationQualified : Option ReclaimCut := none
  deriving Repr

def ReclaimQualified (expected : ReclaimCut) (o : ReclaimObservation) : Prop :=
  o.current = some expected ∧ o.noReaders = some expected ∧
  o.retentionRelease = some expected ∧ o.preservationQualified = some expected

theorem stale_reclaim_cut_rejected (expected observed : ReclaimCut)
    (h : observed ≠ expected) (o : ReclaimObservation)
    (hCurrent : o.current = some observed) :
    ¬ ReclaimQualified expected o := by
  simp [ReclaimQualified, hCurrent, h]

theorem unknown_retention_rejected (expected : ReclaimCut) (o : ReclaimObservation)
    (h : o.retentionRelease = none) :
    ¬ ReclaimQualified expected o := by
  simp [ReclaimQualified, h]

theorem missing_preservation_witness_rejected (expected : ReclaimCut)
    (o : ReclaimObservation) (h : o.preservationQualified = none) :
    ¬ ReclaimQualified expected o := by
  simp [ReclaimQualified, h]

theorem missing_reader_census_rejected (expected : ReclaimCut)
    (o : ReclaimObservation) (h : o.noReaders = none) :
    ¬ ReclaimQualified expected o := by
  simp [ReclaimQualified, h]

theorem exact_reclaim_witnesses_qualify (r : ReclaimCut) :
    ReclaimQualified r ⟨some r, some r, some r, some r⟩ := by
  simp [ReclaimQualified]

-- Necessary scratch-carrier guard, not an atomic filesystem fence.
def ScratchIdentityMatches (created : Nat) (current : Option Nat) : Prop :=
  current = some created

theorem replaced_scratch_not_owned (created current : Nat) (h : current ≠ created) :
    ¬ ScratchIdentityMatches created (some current) := by
  simp [ScratchIdentityMatches, h]

theorem unobserved_scratch_not_owned (created : Nat) :
    ¬ ScratchIdentityMatches created none := by simp [ScratchIdentityMatches]

theorem same_scratch_identity_matches (created : Nat) :
    ScratchIdentityMatches created (some created) := rfl

#print axioms stale_reclaim_cut_rejected
#print axioms unknown_retention_rejected
#print axioms missing_preservation_witness_rejected
#print axioms missing_reader_census_rejected
#print axioms exact_reclaim_witnesses_qualify
#print axioms replaced_scratch_not_owned
#print axioms unobserved_scratch_not_owned
#print axioms same_scratch_identity_matches
#print axioms all_reachable_safe
#print axioms published_requires_validation_and_commit
#print axioms reclaimed_requires_no_readers_and_retention_release
#print axioms direct_publication_without_checks_is_unsafe
end OrdivonDataPublication

-- Identity refinement for Runtime-backed publication claims. Nat is an
-- abstract exact claim key (not a hash or an alternate storage authority).
-- Evidence booleans stand for independently established owner facts; this
-- model does NOT authenticate those facts or implement a physical release.
-- Concrete refinement coordinate: Runtime's authority + exact claim_id and
-- bound (principal, client_request_id, store_root, run_ref, source state).
-- The native schema has unique (principal, client_request_id), primary claim_id;
-- this model assumes the mapping remains injective across the qualified epoch.
-- A new epoch or reused identity cannot consume old witness evidence.
-- A Boolean true means a qualified independent observation, not a caller's
-- assertion; false includes absent/unknown evidence, not falsified business truth.
-- Runtime's raw release function is deliberately NOT claimed to implement
-- this gate. The natural authenticated Finalizer must qualify both witnesses.
-- See services/runtime/docs/workspace-runtime-claim-r1.md.

namespace OrdivonDataPublication.RuntimeBackedClaim

structure Ledger where
  held : Nat → Bool
  retired : Bool
  retentionCleared : Bool

structure ReleaseWitness where
  key : Nat
  domainDispositionAccepted : Bool
  noFutureSpawn : Bool

def release (s : Ledger) (requested : Nat) (w : ReleaseWitness) : Ledger :=
  if w.key == requested && w.domainDispositionAccepted && w.noFutureSpawn then
    { s with held := fun k => if k == requested then false else s.held k }
  else s

def Reclaimable (s : Ledger) : Prop :=
  s.retired = true ∧ s.retentionCleared = true ∧ ∀ k, s.held k = false

theorem unrelated_claim_frame (s : Ledger) (requested other : Nat)
    (w : ReleaseWitness) (h : other ≠ requested) :
    (release s requested w).held other = s.held other := by
  unfold release
  split <;> simp_all

theorem wrong_key_cannot_release (s : Ledger) (requested : Nat)
    (w : ReleaseWitness) (h : w.key ≠ requested) :
    release s requested w = s := by
  simp [release, h]

theorem absent_domain_disposition_cannot_release (s : Ledger) (requested : Nat)
    (w : ReleaseWitness) (h : w.domainDispositionAccepted = false) :
    release s requested w = s := by
  simp [release, h]

theorem absent_no_future_spawn_cannot_release (s : Ledger) (requested : Nat)
    (w : ReleaseWitness) (h : w.noFutureSpawn = false) :
    release s requested w = s := by
  simp [release, h]

theorem replay_same_claim_idempotent (s : Ledger) (requested key : Nat)
    (w : ReleaseWitness) :
    (release (release s requested w) requested w).held key =
      (release s requested w).held key := by
  unfold release
  split <;> simp_all

theorem cannot_reclaim_with_unrelated_held (s : Ledger)
    (requested other : Nat) (w : ReleaseWitness)
    (hne : other ≠ requested) (hHeld : s.held other = true) :
    ¬ Reclaimable (release s requested w) := by
  intro h
  have he := h.2.2 other
  rw [unrelated_claim_frame s requested other w hne, hHeld] at he
  contradiction

theorem qualified_release_clears_only_requested (s : Ledger) (requested : Nat)
    (w : ReleaseWitness) (hk : w.key = requested)
    (hd : w.domainDispositionAccepted = true) (hn : w.noFutureSpawn = true) :
    (release s requested w).held requested = false := by
  simp [release, hk, hd, hn]

theorem release_preserves_retirement_authority (s : Ledger) (requested : Nat)
    (w : ReleaseWitness) :
    (release s requested w).retired = s.retired ∧
      (release s requested w).retentionCleared = s.retentionCleared := by
  unfold release
  split <;> simp_all

-- Non-vacuity: two different claims; replaying one does not release the
-- second. The legitimate independent second release can permit retirement.
def twoClaims : Ledger :=
  { held := fun k => k == 1 || k == 2, retired := true, retentionCleared := true }

def accepted (k : Nat) : ReleaseWitness :=
  { key := k, domainDispositionAccepted := true, noFutureSpawn := true }

theorem duplicate_one_does_not_reclaim :
    ¬ Reclaimable (release (release twoClaims 1 (accepted 1)) 1 (accepted 1)) := by
  intro h
  have he := h.2.2 2
  simp [release, twoClaims, accepted] at he

theorem independent_two_can_reclaim :
    Reclaimable (release (release twoClaims 1 (accepted 1)) 2 (accepted 2)) := by
  refine ⟨rfl, rfl, ?_⟩
  intro k
  by_cases h1 : k = 1
  · simp [release, twoClaims, accepted, h1]
  · by_cases h2 : k = 2
    · simp [release, twoClaims, accepted, h2]
    · simp [release, twoClaims, accepted, h1, h2]

#print axioms qualified_release_clears_only_requested
#print axioms release_preserves_retirement_authority
#print axioms unrelated_claim_frame
#print axioms wrong_key_cannot_release
#print axioms absent_domain_disposition_cannot_release
#print axioms absent_no_future_spawn_cannot_release
#print axioms replay_same_claim_idempotent
#print axioms cannot_reclaim_with_unrelated_held
#print axioms duplicate_one_does_not_reclaim
#print axioms independent_two_can_reclaim
end OrdivonDataPublication.RuntimeBackedClaim
