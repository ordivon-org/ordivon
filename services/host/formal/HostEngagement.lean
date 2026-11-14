-- Agent-facing Host Engagement transition safety, refined against
-- Rust work::engagement::transition (2026-11). The transition system is
-- abstract: no claim of Rust source refinement, PostgreSQL CAS, signed
-- Principal→Actor identity, Artifact validation or deployment currentness.
-- The Action explicitly carries the caller/claimEpoch so forged/stale
-- caller requests cannot disappear from the formal specification.

namespace OrdivonHostEngagement

def maxSafeClaimEpoch : Nat := 9007199254740991

inductive Phase where
  | offered | claimed | submitted | returned | accepted | cancelled
  deriving DecidableEq, Repr

inductive Action where
  | claim (actor : Nat)
  | release (actor : Nat)
  | submit (actor assertedEpoch : Nat)
  | review (actor assertedEpoch : Nat) (accept : Bool)
  | cancel (actor : Nat)
  deriving DecidableEq, Repr

structure State where
  phase : Phase
  epoch : Nat
  assignee : Option Nat
  submittedEpoch : Option Nat
  verificationEpoch : Option Nat
  requester : Nat
  consumer : Nat
  deriving Repr

def initial (requester consumer : Nat) : State :=
  State.mk .offered 0 none none none requester consumer

def claimed (s : State) (worker : Nat) : State :=
  State.mk .claimed (s.epoch + 1) (some worker) none none s.requester s.consumer

def released (s : State) : State :=
  State.mk .offered s.epoch none none none s.requester s.consumer

def submitted (s : State) : State :=
  State.mk .submitted s.epoch s.assignee (some s.epoch) none s.requester s.consumer

def returned (s : State) : State :=
  State.mk .returned s.epoch s.assignee s.submittedEpoch (some s.epoch)
    s.requester s.consumer

def accepted (s : State) : State :=
  State.mk .accepted s.epoch s.assignee s.submittedEpoch (some s.epoch)
    s.requester s.consumer

def cancelled (s : State) : State :=
  State.mk .cancelled s.epoch s.assignee s.submittedEpoch s.verificationEpoch
    s.requester s.consumer

-- A Step is one already-accepted Host Work transition. Each constructor
-- mirrors a phase/Actor/epoch guard from the Rust domain function.
-- One actual SQL revision CAS winner is a separate implementation obligation.
inductive Step : State → Action → State → Prop where
  | claim (s : State) (actor : Nat)
      (hphase : s.phase = .offered ∨ s.phase = .returned)
      (hbound : s.epoch < maxSafeClaimEpoch) :
      Step s (.claim actor) (claimed s actor)
  | release (s : State) (actor : Nat)
      (hphase : s.phase = .claimed)
      (hcaller : actor = s.requester ∨ s.assignee = some actor) :
      Step s (.release actor) (released s)
  | submit (s : State) (actor assertedEpoch : Nat)
      (hphase : s.phase = .claimed)
      (hcaller : s.assignee = some actor)
      (hepoch : assertedEpoch = s.epoch) :
      Step s (.submit actor assertedEpoch) (submitted s)
  | returnForRevision (s : State) (reviewer assertedEpoch : Nat)
      (hphase : s.phase = .submitted)
      (hconsumer : reviewer = s.consumer)
      (hepoch : assertedEpoch = s.epoch)
      (hdelivery : s.submittedEpoch = some s.epoch) :
      Step s (.review reviewer assertedEpoch false) (returned s)
  | accept (s : State) (reviewer assertedEpoch : Nat)
      (hphase : s.phase = .submitted)
      (hconsumer : reviewer = s.consumer)
      (hepoch : assertedEpoch = s.epoch)
      (hdelivery : s.submittedEpoch = some s.epoch) :
      Step s (.review reviewer assertedEpoch true) (accepted s)
  | cancel (s : State) (actor : Nat)
      (hphase : s.phase ≠ .accepted ∧ s.phase ≠ .cancelled)
      (hcaller : actor = s.requester) :
      Step s (.cancel actor) (cancelled s)

def AcceptedHasEvidence (s : State) : Prop :=
  s.phase = .accepted →
    s.submittedEpoch = some s.epoch ∧
    s.verificationEpoch = some s.epoch

theorem step_acceptance_safety {s t : State} {a : Action}
    (h : Step s a t) : AcceptedHasEvidence t := by
  cases h with
  | claim _ _ _ =>
      intro impossible
      cases impossible
  | release _ _ _ =>
      intro impossible
      cases impossible
  | submit _ _ _ _ _ =>
      intro impossible
      cases impossible
  | returnForRevision _ _ _ _ _ _ =>
      intro impossible
      cases impossible
  | accept _ _ _ _ _ hdelivery =>
      intro _
      exact ⟨hdelivery, rfl⟩
  | cancel _ _ _ =>
      intro impossible
      cases impossible

inductive Reachable (origin : State) : State → Prop where
  | here : Reachable origin origin
  | later {s t : State} {a : Action} :
      Reachable origin s → Step s a t → Reachable origin t

theorem reachable_acceptance_safety {requester consumer : Nat} {s : State}
    (h : Reachable (initial requester consumer) s) :
    AcceptedHasEvidence s := by
  induction h with
  | here =>
      intro impossible
      cases impossible
  | later earlier step ih =>
      exact step_acceptance_safety step

-- Admission proofs explicitly inspect the *action argument*, rather than
-- proving a postcondition that could be reached by forged caller metadata.
theorem review_accept_requires_designated_consumer_and_current_epoch
    {s t : State} {actor epoch : Nat}
    (h : Step s (.review actor epoch true) t) :
    actor = s.consumer ∧ epoch = s.epoch := by
  cases h with
  | accept _ _ _ hconsumer hepoch _ =>
      exact ⟨hconsumer, hepoch⟩

theorem release_requires_requester_or_assignee
    {s t : State} {actor : Nat}
    (h : Step s (.release actor) t) :
    actor = s.requester ∨ s.assignee = some actor := by
  cases h with
  | release _ _ hcaller =>
      exact hcaller

theorem cancel_requires_requester
    {s t : State} {actor : Nat}
    (h : Step s (.cancel actor) t) : actor = s.requester := by
  cases h with
  | cancel _ _ hcaller =>
      exact hcaller

theorem accept_preserves_epoch (s : State) :
    (accepted s).epoch = s.epoch := by
  rfl

theorem claim_advances_epoch (s : State) (worker : Nat) :
    (claimed s worker).epoch = s.epoch + 1 := by
  rfl

theorem claim_clears_prior_delivery (s : State) (worker : Nat) :
    (claimed s worker).submittedEpoch = none ∧
    (claimed s worker).verificationEpoch = none := by
  exact ⟨rfl, rfl⟩

-- The abstract model cannot assert a fake accepted Work, even if someone
-- wrote the value directly rather than passing the transition guard.
def fabricatedAccepted : State :=
  State.mk .accepted 1 (some 7) none (some 1) 17 19

theorem fabricated_acceptance_is_rejected :
    ¬ AcceptedHasEvidence fabricatedAccepted := by
  intro assumed
  have h : (fabricatedAccepted.submittedEpoch = some fabricatedAccepted.epoch) :=
    (assumed rfl).1
  cases h

#print axioms step_acceptance_safety
#print axioms reachable_acceptance_safety
#print axioms review_accept_requires_designated_consumer_and_current_epoch
#print axioms release_requires_requester_or_assignee
#print axioms cancel_requires_requester
#print axioms accept_preserves_epoch
#print axioms claim_advances_epoch
#print axioms claim_clears_prior_delivery
#print axioms fabricated_acceptance_is_rejected

end OrdivonHostEngagement
