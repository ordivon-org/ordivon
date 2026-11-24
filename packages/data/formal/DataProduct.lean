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

-- Selected output integrity is a consumer-scoped decision, not a summary
-- of unrelated ports. The caller has already resolved and uniquely identified
-- the requested product/version/port set. This model proves only its verdict
-- aggregation, not exact lookup or physical file reads.
def selectedAdmissible (selected : List Verdict) : Bool :=
  !selected.isEmpty && selected.all (fun verdict => verdict == .verified)

theorem no_empty_selected_admission :
    selectedAdmissible [] = false := by
  rfl

theorem selected_admission_requires_nonempty
    (selected : List Verdict) (h : selectedAdmissible selected = true) :
    selected ≠ [] := by
  intro empty
  subst selected
  simp [selectedAdmissible] at h

theorem selected_admission_requires_verified
    (selected : List Verdict) (h : selectedAdmissible selected = true)
    (verdict : Verdict) (member : verdict ∈ selected) :
    verdict = .verified := by
  have hall : selected.all (fun v => v == .verified) = true := by
    cases hAll : selected.all (fun v => v == .verified) with
    | false => simp [selectedAdmissible, hAll] at h
    | true => rfl
  have hv : (verdict == .verified) = true :=
    List.all_eq_true.mp hall verdict member
  exact beq_iff_eq.mp hv

theorem selected_falsified_cannot_pass
    (selected : List Verdict) (h : Verdict.falsified ∈ selected) :
    selectedAdmissible selected = false := by
  cases gate : selectedAdmissible selected with
  | false => rfl
  | true =>
    have impossible := selected_admission_requires_verified selected gate .falsified h
    cases impossible

theorem selected_unknown_cannot_pass
    (selected : List Verdict) (h : Verdict.unknown ∈ selected) :
    selectedAdmissible selected = false := by
  cases gate : selectedAdmissible selected with
  | false => rfl
  | true =>
    have impossible := selected_admission_requires_verified selected gate .unknown h
    cases impossible

-- Explicit counterexample to accidental catalog-wide admission:
-- the selected port is verified, the unrelated port is falsified.
example : selectedAdmissible [.verified] = true := by decide
example : selectedAdmissible [.verified, .falsified] = false := by decide

-- Bitol ODPS 1.1 output port identity is (name, optional version);
-- optional port UUID is not the required logical key. The whole data
-- product ID/version is fixed by the calling product projection.
abbrev PortKey := String × Option String

-- Unlike the earlier selectedAdmissible model, exactPortVerdict models
-- the *selection* step. Missing or ambiguous exact keys do not yield a
-- verified verdict. This is abstract selection, not Python/source proof.
def exactPortVerdict (requested : PortKey)
    (rows : List (PortKey × Verdict)) : Option Verdict :=
  match rows.filter (fun row => row.1 == requested) with
  | [(_, verdict)] => some verdict
  | _ => none

theorem exactPortVerdict_unrelated_frame (requested other : PortKey)
    (rows : List (PortKey × Verdict)) (verdict : Verdict)
    (h : other ≠ requested) :
    exactPortVerdict requested (rows ++ [(other, verdict)]) =
      exactPortVerdict requested rows := by
  simp [exactPortVerdict, List.filter_append, h]

-- The qualified Research v1 port remains selected when a same-name
-- v2 port exists. A sole wrong version or duplicate matching key
-- cannot satisfy exact selection.
example :
    exactPortVerdict ("manifest", some "1.0.0")
      [(("manifest", some "1.0.0"), .verified),
       (("manifest", some "2.0.0"), .falsified)] = some .verified := by
  decide

example :
    exactPortVerdict ("manifest", some "1.0.0")
      [(("manifest", some "2.0.0"), .verified)] = none := by
  decide

example :
    exactPortVerdict ("manifest", some "1.0.0")
      [(("manifest", some "1.0.0"), .verified),
       (("manifest", some "1.0.0"), .verified)] = none := by
  decide

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
#print axioms selected_admission_requires_nonempty
#print axioms selected_admission_requires_verified
#print axioms selected_falsified_cannot_pass
#print axioms selected_unknown_cannot_pass
#print axioms exactPortVerdict_unrelated_frame
end OrdivonData
