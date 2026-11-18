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

#print axioms all_reachable_safe
#print axioms published_requires_validation_and_commit
#print axioms reclaimed_requires_no_readers_and_retention_release
#print axioms direct_publication_without_checks_is_unsafe
end OrdivonDataPublication
