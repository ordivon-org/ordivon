-- Bounded two-generation publication/refcount control model.
-- Thought LEGO only: this is NOT a PG isolation, runtime, lease, or Artifact
-- implementation refinement. Retention is a declaration from its Owner.
namespace OrdivonDataMultiVersion

structure State where
  activeNew : Bool := false
  newValidated : Bool := false
  newCommitted : Bool := false
  oldReaders : Nat := 0
  newReaders : Nat := 0
  oldRetentionCleared : Bool := false
  oldReclaimed : Bool := false
  deriving Repr

def initial : State := {}

-- Old is an already committed source version; the next generation starts
-- unverified and cannot be made visible before verification and commit.
def Safety (s : State) : Prop :=
  (s.activeNew = true → s.newValidated = true ∧ s.newCommitted = true) ∧
  (s.oldReclaimed = true →
    s.activeNew = true ∧ s.oldReaders = 0 ∧ s.oldRetentionCleared = true) ∧
  (s.activeNew = false → s.oldReclaimed = false)

-- All transitions are abstractly atomic. Real physical commit and leases
-- must be refined by producer's PostgreSQL and Artifact/consumer evidence.
inductive Step : State → State → Prop where
  | validate (s : State) :
      Step s {s with newValidated := true}
  | commit (s : State) (h : s.newValidated = true) :
      Step s {s with newCommitted := true}
  | switch (s : State)
      (hValidated : s.newValidated = true)
      (hCommitted : s.newCommitted = true) :
      Step s {s with activeNew := true}
  | acquireOld (s : State) (h : s.activeNew = false) :
      Step s {s with oldReaders := s.oldReaders + 1}
  | acquireNew (s : State) (h : s.activeNew = true) :
      Step s {s with newReaders := s.newReaders + 1}
  | releaseOld (s : State) (h : s.oldReaders > 0) :
      Step s {s with oldReaders := s.oldReaders - 1}
  | releaseNew (s : State) (h : s.newReaders > 0) :
      Step s {s with newReaders := s.newReaders - 1}
  | clearOldRetention (s : State) (h : s.activeNew = true) :
      Step s {s with oldRetentionCleared := true}
  | reclaimOld (s : State)
      (hHead : s.activeNew = true)
      (hReaders : s.oldReaders = 0)
      (hRetention : s.oldRetentionCleared = true) :
      Step s {s with oldReclaimed := true}

theorem initial_safe : Safety initial := by
  simp [Safety, initial]

theorem step_preserves_safety {s t : State}
    (hSafe : Safety s) (hStep : Step s t) : Safety t := by
  cases hStep <;> simp_all [Safety]

inductive Reachable : State → Prop where
  | initial : Reachable OrdivonDataMultiVersion.initial
  | step {s t : State} : Reachable s → Step s t → Reachable t

theorem all_reachable_safe {s : State} (h : Reachable s) : Safety s := by
  induction h with
  | initial => exact initial_safe
  | step _ hstep ih => exact step_preserves_safety ih hstep

theorem published_v2_requires_validation_and_commit {s : State}
    (h : Reachable s) (hPublished : s.activeNew = true) :
    s.newValidated = true ∧ s.newCommitted = true :=
  (all_reachable_safe h).1 hPublished

theorem reclaimed_v1_requires_grace_and_retention {s : State}
    (h : Reachable s) (hReclaimed : s.oldReclaimed = true) :
    s.activeNew = true ∧ s.oldReaders = 0 ∧ s.oldRetentionCleared = true :=
  (all_reachable_safe h).2.1 hReclaimed

-- Snapshot pointer swap does not revoke a previously-acquired V1 lease.
theorem switch_preserves_existing_old_reader_lease (s : State)
    (_hValid : s.newValidated = true)
    (_hCommitted : s.newCommitted = true) :
    ({s with activeNew := true} : State).oldReaders = s.oldReaders := by
  rfl

-- Invalid transitions are intentionally NOT steps; counterexamples to Safety
-- show what would happen if external code nevertheless exposed the new head
-- or erased still-readable old-version bytes.
def unsafeDirectSwitch : State := {initial with activeNew := true}
theorem uncommitted_direct_switch_violates_safety :
    ¬ Safety unsafeDirectSwitch := by
  simp [Safety, unsafeDirectSwitch, initial]

def unsafeEarlyReclaim : State :=
  { activeNew := true, newValidated := true, newCommitted := true,
    oldReaders := 1, oldRetentionCleared := true, oldReclaimed := true }

theorem reclaim_with_outstanding_old_reader_violates_safety :
    ¬ Safety unsafeEarlyReclaim := by
  simp [Safety, unsafeEarlyReclaim]

-- Nonvacuity witness: real readers may remain pinned to V1 *after* V2 is
-- published, without requiring them to reopen V2 or releasing them early.
theorem reachable_old_reader_after_v2_switch :
    ∃ s : State, Reachable s ∧ s.activeNew = true ∧
      s.oldReaders = 1 ∧ s.oldReclaimed = false := by
  let s1 : State := {initial with oldReaders := 1}
  let s2 : State := {s1 with newValidated := true}
  let s3 : State := {s2 with newCommitted := true}
  let s4 : State := {s3 with activeNew := true}
  have h1 : Reachable s1 := by
    apply Reachable.step Reachable.initial
    simpa [s1, initial] using Step.acquireOld initial (by decide)
  have h2 : Reachable s2 := by
    apply Reachable.step h1
    simpa [s2] using Step.validate s1
  have h3 : Reachable s3 := by
    apply Reachable.step h2
    simpa [s3] using Step.commit s2 (by simp [s2])
  have h4 : Reachable s4 := by
    apply Reachable.step h3
    simpa [s4] using Step.switch s3 (by simp [s3, s2])
      (by simp [s3])
  refine ⟨s4, h4, ?_, ?_, ?_⟩
  · simp [s4]
  · simp [s4, s3, s2, s1]
  · simp [s4, s3, s2, s1, initial]

-- Release of both old-reader and retention obligations makes old-version
-- reclamation reachable, but does not prescribe who authorizes retention.
theorem reachable_reclaim_after_grace_and_retention :
    ∃ s : State, Reachable s ∧ s.oldReclaimed = true ∧
      s.oldReaders = 0 ∧ s.activeNew = true := by
  let s1 : State := {initial with oldReaders := 1}
  let s2 : State := {s1 with newValidated := true}
  let s3 : State := {s2 with newCommitted := true}
  let s4 : State := {s3 with activeNew := true}
  let s5 : State := {s4 with oldRetentionCleared := true}
  let s6 : State := {s5 with oldReaders := 0}
  let s7 : State := {s6 with oldReclaimed := true}
  have h1 : Reachable s1 := by
    apply Reachable.step Reachable.initial
    simpa [s1, initial] using Step.acquireOld initial (by decide)
  have h2 : Reachable s2 := by
    apply Reachable.step h1
    simpa [s2] using Step.validate s1
  have h3 : Reachable s3 := by
    apply Reachable.step h2
    simpa [s3] using Step.commit s2 (by simp [s2])
  have h4 : Reachable s4 := by
    apply Reachable.step h3
    simpa [s4] using Step.switch s3 (by simp [s3, s2])
      (by simp [s3])
  have h5 : Reachable s5 := by
    apply Reachable.step h4
    simpa [s5] using Step.clearOldRetention s4 (by simp [s4])
  have h6 : Reachable s6 := by
    apply Reachable.step h5
    simpa [s6, s5, s4, s3, s2, s1, initial] using
      Step.releaseOld s5 (by simp [s5, s4, s3, s2, s1])
  have h7 : Reachable s7 := by
    apply Reachable.step h6
    simpa [s7] using Step.reclaimOld s6
      (by simp [s6, s5, s4])
      (by simp [s6])
      (by simp [s6, s5])
  refine ⟨s7, h7, ?_, ?_, ?_⟩
  · simp [s7]
  · simp [s7, s6]
  · simp [s7, s6, s5, s4]

#print axioms all_reachable_safe
#print axioms published_v2_requires_validation_and_commit
#print axioms reclaimed_v1_requires_grace_and_retention
#print axioms uncommitted_direct_switch_violates_safety
#print axioms reclaim_with_outstanding_old_reader_violates_safety
#print axioms reachable_old_reader_after_v2_switch
#print axioms reachable_reclaim_after_grace_and_retention
end OrdivonDataMultiVersion
