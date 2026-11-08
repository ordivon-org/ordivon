-- Data product identity and digest-observation state, a bounded semantic model.
-- This is a proof about abstract metadata; installed Python, network, SHA-256,
-- filesystem path races and domain data quality need separate refinement evidence.
namespace OrdivonData

inductive Verdict where
  | unknown
  | verified
  | falsified
  deriving DecidableEq, Repr

-- Two optional abstract digests. A missing authoritative binding or
-- observation is not evidence of a mismatch.
def digestVerdict (declared observed : Option Nat) : Verdict :=
  match declared, observed with
  | some expected, some actual =>
    if expected = actual then .verified else .falsified
  | _, _ => .unknown

theorem no_declared_digest (observed : Option Nat) :
    digestVerdict none observed = .unknown := by
  cases observed <;> rfl

theorem no_observed_digest (declared : Option Nat) :
    digestVerdict declared none = .unknown := by
  cases declared <;> rfl

theorem identical_digests_are_verified (digest : Nat) :
    digestVerdict (some digest) (some digest) = .verified := by
  simp [digestVerdict]

theorem different_digests_are_falsified
    (declared observed : Nat) (h : declared ≠ observed) :
    digestVerdict (some declared) (some observed) = .falsified := by
  simp [digestVerdict, h]

theorem verified_requires_equal_observed_digests
    (declared observed : Option Nat)
    (h : digestVerdict declared observed = .verified) :
    ∃ digest, declared = some digest ∧ observed = some digest := by
  cases declared with
  | none => simp [digestVerdict] at h
  | some d =>
    cases observed with
    | none => simp [digestVerdict] at h
    | some o =>
      by_cases hEqual : d = o
      · subst o
        exact ⟨d, rfl, rfl⟩
      · simp [digestVerdict, hEqual] at h

theorem falsified_requires_two_different_observed_digests
    (declared observed : Option Nat)
    (h : digestVerdict declared observed = .falsified) :
    ∃ d o, declared = some d ∧ observed = some o ∧ d ≠ o := by
  cases declared with
  | none => simp [digestVerdict] at h
  | some d =>
    cases observed with
    | none => simp [digestVerdict] at h
    | some o =>
      by_cases hEqual : d = o
      · simp [digestVerdict, hEqual] at h
      · exact ⟨d, o, rfl, rfl, hEqual⟩

-- The key is the *whole* product identity and version pair; older versions
-- remain distinct. The model is a list with decidable exact equality, not a
-- replacement registry or data storage implementation.
abbrev ProductIdentity := String × String

def admitUnique (known : List ProductIdentity) (candidate : ProductIdentity) :
    Option (List ProductIdentity) :=
  if candidate ∈ known then none else some (candidate :: known)

theorem existing_product_version_is_rejected
    (known : List ProductIdentity) (candidate : ProductIdentity)
    (h : candidate ∈ known) :
    admitUnique known candidate = none := by
  simp [admitUnique, h]

theorem admitting_new_version_preserves_unique_identity
    (known : List ProductIdentity) (candidate : ProductIdentity)
    (hKnown : known.Nodup) (next : List ProductIdentity)
    (hAdmitted : admitUnique known candidate = some next) :
    next.Nodup := by
  by_cases hIn : candidate ∈ known
  · simp [admitUnique, hIn] at hAdmitted
  · simp [admitUnique, hIn] at hAdmitted
    cases hAdmitted
    exact List.nodup_cons.mpr ⟨hIn, hKnown⟩

#print axioms verified_requires_equal_observed_digests
#print axioms falsified_requires_two_different_observed_digests
#print axioms admitting_new_version_preserves_unique_identity
end OrdivonData
