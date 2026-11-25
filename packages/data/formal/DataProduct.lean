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

-- Inverse uniqueness: distinct surface spellings may denote the same
-- projected UUID. Compare the semantic key before admission, not the spelling.
-- The normalization function abstracts the existing native UUID parser;
-- opaque identifiers are not globally lowercased. Versions remain independent.
def projectedProductKey (normalize : String → String)
    (candidate : ProductIdentity) : ProductIdentity :=
  (normalize candidate.1, candidate.2)

def admitProjectedUnique (normalize : String → String)
    (known : List ProductIdentity) (candidate : ProductIdentity) :
    Option (List ProductIdentity) :=
  admitUnique (known.map (projectedProductKey normalize))
    (projectedProductKey normalize candidate)

theorem projected_alias_same_version_rejected
    (normalize : String → String) (a b version : String)
    (alias : normalize a = normalize b) :
    admitProjectedUnique normalize [(a, version)] (b, version) = none := by
  simp [admitProjectedUnique, projectedProductKey, admitUnique, alias]

theorem projected_distinct_version_admitted
    (normalize : String → String) (a b v1 v2 : String)
    (different : v2 ≠ v1) :
    admitProjectedUnique normalize [(a, v1)] (b, v2) =
      some [(normalize b, v2), (normalize a, v1)] := by
  simp [admitProjectedUnique, projectedProductKey, admitUnique, different]

-- Product binding operates on canonical identities, before physical evidence.
-- Omitted version means a unique matching product, not all its versions.
def selectProductVersion (id : String) (version : Option String)
    (rows : List ProductIdentity) : Option ProductIdentity :=
  match rows.filter (fun row =>
    row.1 == id && (match version with
      | none => true
      | some v => row.2 == v)) with
  | [row] => some row
  | _ => none

theorem omitted_product_version_rejects_two
    (id v1 v2 : String) :
    selectProductVersion id none [(id, v1), (id, v2)] = none := by
  simp [selectProductVersion]

theorem exact_product_version_selects_only_one
    (id v1 v2 : String) (h : v1 ≠ v2) :
    selectProductVersion id (some v2) [(id, v1), (id, v2)] =
      some (id, v2) := by
  simp [selectProductVersion, h]

theorem unrelated_product_version_frame
    (id requested other : String) (rows : List ProductIdentity)
    (h : other ≠ requested) :
    selectProductVersion id (some requested) (rows ++ [(id, other)]) =
      selectProductVersion id (some requested) rows := by
  simp [selectProductVersion, List.filter_append, h]

#print axioms omitted_product_version_rejects_two
#print axioms exact_product_version_selects_only_one
#print axioms unrelated_product_version_frame

-- Discovery may contain anonymous rows. Only explicit IDs participate
-- in the uniqueness obligation. Payload equality never merges identities.
def explicitDistributionIds (rows : List (Option String × Nat)) : List String :=
  rows.filterMap (fun row => row.1)

def distributionIdentityQualified (rows : List (Option String × Nat)) : Prop :=
  (explicitDistributionIds rows).Nodup

theorem duplicate_distribution_id_rejected (id : String) (a b : Nat) :
    ¬ distributionIdentityQualified [(some id, a), (some id, b)] := by
  simp [distributionIdentityQualified, explicitDistributionIds]

theorem same_payload_distinct_ids_not_redundancy (a b : String) (digest : Nat)
    (distinct : a ≠ b) :
    distributionIdentityQualified [(some a, digest), (some b, digest)] := by
  simp [distributionIdentityQualified, explicitDistributionIds, distinct]

#print axioms duplicate_distribution_id_rejected
#print axioms same_payload_distinct_ids_not_redundancy
-- Abstract one decoded object, before any last-wins dictionary conversion.
-- A decoder supplies decoded key spelling and finite-number qualification.
-- Each nested object must independently satisfy this same predicate.
def metadataObjectQualified (members : List (String × Nat))
    (finite : Bool) : Prop :=
  (members.map Prod.fst).Nodup ∧ finite = true

theorem repeated_metadata_member_rejected (key : String) (a b : Nat)
    (finite : Bool) :
    ¬ metadataObjectQualified [(key, a), (key, b)] finite := by
  simp [metadataObjectQualified]

theorem nonfinite_metadata_rejected (members : List (String × Nat)) :
    ¬ metadataObjectQualified members false := by
  simp [metadataObjectQualified]

theorem distinct_finite_members_qualified (a b : String) (x y : Nat)
    (h : a ≠ b) : metadataObjectQualified [(a, x), (b, y)] true := by
  simp [metadataObjectQualified, h]

#print axioms repeated_metadata_member_rejected
#print axioms nonfinite_metadata_rejected
#print axioms distinct_finite_members_qualified

#print axioms projected_alias_same_version_rejected
#print axioms projected_distinct_version_admitted

#print axioms verified_requires_equal_observed_digests
#print axioms falsified_requires_two_different_observed_digests
#print axioms admitting_new_version_preserves_unique_identity
#print axioms selected_admission_requires_nonempty
#print axioms selected_admission_requires_verified
#print axioms selected_falsified_cannot_pass
#print axioms selected_unknown_cannot_pass
#print axioms exactPortVerdict_unrelated_frame
-- Reuse the existing all-or-nothing finite-list operator for metadata
-- preparation. The Option payload now denotes qualified path/digest
-- coordinates, not observed blobs or a physical file availability claim.
abbrev prepareEvidenceBatch := localBlobSnapshot

theorem prepareEvidenceBatch_missing_rejects
    (rows : List (Option Nat)) (h : none ∈ rows) :
    prepareEvidenceBatch rows = none :=
  missing_local_blob_rejects rows h

theorem prepareEvidenceBatch_complete
    (rows : List Nat) :
    prepareEvidenceBatch (rows.map some) = some rows :=
  complete_local_snapshot rows

theorem prepareEvidenceBatch_no_omission
    (rows : List (Option Nat)) (plan : List Nat)
    (h : prepareEvidenceBatch rows = some plan) :
    rows = plan.map some :=
  local_snapshot_has_no_omitted_blob rows plan h

#print axioms prepareEvidenceBatch_missing_rejects
#print axioms prepareEvidenceBatch_complete
#print axioms prepareEvidenceBatch_no_omission

end OrdivonData
