-- Host Agent Work Engagement: finite-action, unbounded-epoch abstract safety.
-- Not a statement about installed PostgreSQL, Access Principal authorization,
-- Runtime effects or Artifact verification. Rust transitions and actual MCP
-- consumers are independent source/refinement obligations.

namespace OrdivonHostEngagement

inductive Phase where
  | offered | claimed | submitted | returned | accepted | cancelled
  deriving DecidableEq, Repr

structure State where
  phase : Phase
  epoch : Nat
  assignee : Option Nat
  submittedEpoch : Option Nat
  verificationEpoch : Option Nat
  consumer : Nat
  deriving Repr

def initial (consumer : Nat) : State :=
  State.mk .offered 0 none none none consumer

def claimed (s : State) (worker : Nat) : State :=
  State.mk .claimed (s.epoch + 1) (some worker) none none s.consumer

def released (s : State) : State :=
  State.mk .offered s.epoch none none none s.consumer

def submitted (s : State) : State :=
  State.mk .submitted s.epoch s.assignee (some s.epoch) none s.consumer

def returned (s : State) : State :=
  State.mk .returned s.epoch s.assignee s.submittedEpoch (some s.epoch) s.consumer

def accepted (s : State) : State :=
  State.mk .accepted s.epoch s.assignee s.submittedEpoch (some s.epoch) s.consumer

def cancelled (s : State) : State :=
  State.mk .cancelled s.epoch s.assignee s.submittedEpoch s.verificationEpoch s.consumer

-- A Step describes a single already-admitted Host Work revision transition.
-- It assumes external Security binds caller identity to the requested actor,
-- and that PostgreSQL's CAS admits at most one competing write per revision.
inductive Step : State → State → Prop where
  | claim (s : State) (worker : Nat)
      (hphase : s.phase = .offered ∨ s.phase = .returned) :
      Step s (claimed s worker)
  | release (s : State) (worker : Nat)
      (hphase : s.phase = .claimed)
      (howner : s.assignee = some worker) :
      Step s (released s)
  | submit (s : State) (worker : Nat)
      (hphase : s.phase = .claimed)
      (howner : s.assignee = some worker) :
      Step s (submitted s)
  | returnForRevision (s : State) (reviewer : Nat)
      (hphase : s.phase = .submitted)
      (hconsumer : reviewer = s.consumer)
      (hdelivery : s.submittedEpoch = some s.epoch) :
      Step s (returned s)
  | accept (s : State) (reviewer : Nat)
      (hphase : s.phase = .submitted)
      (hconsumer : reviewer = s.consumer)
      (hdelivery : s.submittedEpoch = some s.epoch) :
      Step s (accepted s)
  | cancel (s : State)
      (hactive : s.phase ≠ .accepted ∧ s.phase ≠ .cancelled) :
      Step s (cancelled s)

def AcceptedHasEvidence (s : State) : Prop :=
  s.phase = .accepted →
    s.submittedEpoch = some s.epoch ∧
    s.verificationEpoch = some s.epoch

theorem step_acceptance_safety {s t : State} (h : Step s t) :
    AcceptedHasEvidence t := by
  cases h with
  | claim worker _ =>
      intro impossible
      cases impossible
  | release worker _ _ =>
      intro impossible
      cases impossible
  | submit worker _ _ =>
      intro impossible
      cases impossible
  | returnForRevision reviewer _ _ _ =>
      intro impossible
      cases impossible
  | accept reviewer _ _ hdelivery =>
      intro _
      exact ⟨hdelivery, rfl⟩
  | cancel _ =>
      intro impossible
      cases impossible

inductive Reachable (origin : State) : State → Prop where
  | here : Reachable origin origin
  | later {s t : State} : Reachable origin s → Step s t → Reachable origin t

theorem reachable_acceptance_safety {consumer : Nat} {s : State}
    (h : Reachable (initial consumer) s) : AcceptedHasEvidence s := by
  induction h with
  | here =>
      intro impossible
      cases impossible
  | later earlier step ih =>
      exact step_acceptance_safety step

theorem accept_preserves_epoch (s : State) :
    (accepted s).epoch = s.epoch := by
  rfl

theorem claim_advances_epoch (s : State) (worker : Nat) :
    (claimed s worker).epoch = s.epoch + 1 := by
  rfl

-- Independent negative witness: the safety predicate rejects a fabricated
-- Accepted state which lacks a submitted delivery. A successful Lean compile
-- must not be misreported as a checked Rust/PostgreSQL refinement.
def fabricatedAccepted : State :=
  State.mk .accepted 1 (some 7) none (some 1) 19

theorem fabricated_acceptance_is_rejected :
    ¬ AcceptedHasEvidence fabricatedAccepted := by
  intro assumed
  have h : (fabricatedAccepted.submittedEpoch = some fabricatedAccepted.epoch) :=
    (assumed rfl).1
  cases h

#print axioms fabricated_acceptance_is_rejected
#print axioms step_acceptance_safety
#print axioms reachable_acceptance_safety
#print axioms accept_preserves_epoch
#print axioms claim_advances_epoch

end OrdivonHostEngagement
