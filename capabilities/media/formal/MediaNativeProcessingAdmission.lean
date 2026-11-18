-- Media's native-profile admission model over opaque identity tokens.
-- Kernel-checked MODEL properties. NOT Python implementation refinement,
-- tool-readiness, SHA-256 collision resistance, or publication authority.
namespace OrdivonMedia

structure ProfileSnapshot where
  profileId : Nat
  profileDigest : Nat
  adapterDigest : Nat
  adapterPresent : Bool
  adapterPathPresent : Bool
  deriving DecidableEq, Repr

structure Selection where
  profileId : Nat
  expectedProfileDigest : Nat
  expectedAdapterDigest : Nat
  selectedInput : Bool
  selectedEvidenceDirectory : Bool
  deriving DecidableEq, Repr

def Admissible (p : ProfileSnapshot) (s : Selection) : Prop :=
  p.profileId = s.profileId ∧
  p.profileDigest = s.expectedProfileDigest ∧
  p.adapterDigest = s.expectedAdapterDigest ∧
  p.adapterPresent = true ∧
  p.adapterPathPresent = true ∧
  s.selectedInput = true ∧
  s.selectedEvidenceDirectory = true

-- A source-bound proposal is made only for an admissible selection.
-- The returned value is a proposal, never an effect or publication.
noncomputable def compile (p : ProfileSnapshot) (s : Selection) : Option ProfileSnapshot := by
  classical
  exact if _ : Admissible p s then some p else none

theorem compiled_iff_admissible (p : ProfileSnapshot) (s : Selection) :
    compile p s = some p ↔ Admissible p s := by
  by_cases h : Admissible p s
  · simp [compile, h]
  · simp [compile, h]

theorem compiled_preserves_all_exact_ids (p : ProfileSnapshot) (s : Selection)
    (h : compile p s = some p) :
    p.profileId = s.profileId ∧
    p.profileDigest = s.expectedProfileDigest ∧
    p.adapterDigest = s.expectedAdapterDigest := by
  have hadmit := (compiled_iff_admissible p s).mp h
  exact ⟨hadmit.1, hadmit.2.1, hadmit.2.2.1⟩

theorem stale_profile_digest_rejected (p : ProfileSnapshot) (s : Selection)
    (h : p.profileDigest ≠ s.expectedProfileDigest) :
    compile p s = none := by
  have denied : ¬ Admissible p s := by
    intro hadmit
    exact h hadmit.2.1
  simp [compile, denied]

theorem stale_adapter_digest_rejected (p : ProfileSnapshot) (s : Selection)
    (h : p.adapterDigest ≠ s.expectedAdapterDigest) :
    compile p s = none := by
  have denied : ¬ Admissible p s := by
    intro hadmit
    exact h hadmit.2.2.1
  simp [compile, denied]

theorem missing_adapter_rejected (p : ProfileSnapshot) (s : Selection)
    (h : p.adapterPresent = false) :
    compile p s = none := by
  have denied : ¬ Admissible p s := by
    intro hadmit
    have hp : p.adapterPresent = true := hadmit.2.2.2.1
    simp [h] at hp
  simp [compile, denied]

theorem missing_input_rejected (p : ProfileSnapshot) (s : Selection)
    (h : s.selectedInput = false) :
    compile p s = none := by
  have denied : ¬ Admissible p s := by
    intro hadmit
    have hi : s.selectedInput = true := hadmit.2.2.2.2.2.1
    simp [h] at hi
  simp [compile, denied]

theorem eligible_selection_has_proposal (p : ProfileSnapshot) (s : Selection)
    (h : Admissible p s) : compile p s = some p :=
  (compiled_iff_admissible p s).mpr h

-- This witness demonstrates that unequal abstract digests really are rejected;
-- an unconditional 'some p' compiler would violate the first conjunct.
theorem stale_digest_counterexample :
    ∃ p : ProfileSnapshot, ∃ s : Selection,
      p.profileDigest ≠ s.expectedProfileDigest ∧ compile p s = none := by
  let p : ProfileSnapshot := ⟨1, 1, 2, true, true⟩
  let s : Selection := ⟨1, 3, 2, true, true⟩
  refine ⟨p, s, by decide, ?_⟩
  exact stale_profile_digest_rejected p s (by decide)

structure Standing where
  technicalQcObserved : Bool
  publicationApproved : Bool
  deriving DecidableEq, Repr

-- Media's technical observation has no authority to set publication.
def recordTechnicalEvidence (s : Standing) (accepted : Bool) : Standing :=
  { s with technicalQcObserved := accepted }

theorem technical_evidence_cannot_approve_publication (s : Standing)
    (accepted : Bool) :
    (recordTechnicalEvidence s accepted).publicationApproved =
      s.publicationApproved := by
  rfl

end OrdivonMedia
