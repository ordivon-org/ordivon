import RecursiveLegoRefinement

namespace OrdivonR21

-- Property-scoped frame rule for an environment-dependent LEGO boundary.
-- A source hash alone cannot discharge readset coverage, changed-ref
-- detection, runtime authority or the refinement of the concrete adapter.
-- These are EXPLICIT hypotheses; the Lean kernel only transfers the claim
-- under these hypotheses. This reuses R2.1 contracts, not a new calculus.

def AgreesOn {Ref Value : Type}
    (read : Ref → Prop) (oldEnv newEnv : Ref → Value) : Prop :=
  ∀ ref, read ref → oldEnv ref = newEnv ref

def ReadsetDetermines {Ref Value Observation : Type}
    (read : Ref → Prop)
    (observe : (Ref → Value) → Observation) : Prop :=
  ∀ oldEnv newEnv, AgreesOn read oldEnv newEnv →
    observe oldEnv = observe newEnv

def DirectlyAffected {Ref : Type}
    (read changed : Ref → Prop) : Prop :=
  ∃ ref, read ref ∧ changed ref

-- Negative-miss-free change detection over ALL actual Ref values yields
-- agreement on an obligation's declared readset when no changed root hits it.
theorem no_hit_implies_agreement
    {Ref Value : Type}
    (read changed : Ref → Prop)
    (oldEnv newEnv : Ref → Value)
    (changedCoversDelta : ∀ ref, oldEnv ref ≠ newEnv ref → changed ref)
    (noHit : ¬ DirectlyAffected read changed) :
    AgreesOn read oldEnv newEnv := by
  classical
  intro ref isRead
  apply Classical.byContradiction
  intro differs
  exact noHit ⟨ref, isRead, changedCoversDelta ref differs⟩

-- This is the precise boundary at which a changed implementation can be
-- opaque to a consumer. It does NOT construct the readset or prove
-- ReadsetDetermines for any actual Rust/TS/Python implementation.
theorem property_scoped_reuse_if_frame_qualified
    {Ref Value Observation : Type}
    (read changed : Ref → Prop)
    (oldEnv newEnv : Ref → Value)
    (observe : (Ref → Value) → Observation)
    (consumerProperty : Observation → Prop)
    (readsetComplete : ReadsetDetermines read observe)
    (changedCoversDelta : ∀ ref, oldEnv ref ≠ newEnv ref → changed ref)
    (noHit : ¬ DirectlyAffected read changed)
    (oldProof : consumerProperty (observe oldEnv)) :
    consumerProperty (observe newEnv) := by
  have hAgree :=
    no_hit_implies_agreement read changed oldEnv newEnv changedCoversDelta noHit
  have hSame : observe oldEnv = observe newEnv :=
    readsetComplete oldEnv newEnv hAgree
  exact hSame ▸ oldProof

-- Source declarations are not automatically complete. This is a checked
-- countermodel: untracked authority:credential flips while the tracked
-- config:proxy remains equal, changing the consumer's observed effect.
theorem omitted_dependency_invalidates_unqualified_frame :
    ∃ (read : Bool → Prop) (oldEnv newEnv : Bool → Bool)
      (observe : (Bool → Bool) → Bool),
      AgreesOn read oldEnv newEnv ∧
      observe oldEnv ≠ observe newEnv := by
  refine ⟨(fun ref => ref = false),
    (fun _ => false), (fun ref => ref),
    (fun environment => environment true), ?_, ?_⟩
  · intro ref isRead
    cases ref with
    | false => rfl
    | true => cases isRead
  · decide

-- Interface output alone is NOT full R2.1 behavior: an adapter may return
-- the same Unit response while its external-effect flag changes from
-- "not authorized" to "effect performed". The existing contract refinement
-- law rejects this as a substitution for the old consumer.
theorem data_equal_but_effect_changed_is_not_refinement :
    ∃ (oldContract newContract : IOContract Unit (Unit × Bool)),
      ¬ Refines newContract oldContract := by
  let oldContract : IOContract Unit (Unit × Bool) := {
    assume := fun _ => True
    guarantee := fun _ out => out.2 = false
  }
  let newContract : IOContract Unit (Unit × Bool) := {
    assume := fun _ => True
    guarantee := fun _ out => out.2 = true
  }
  refine ⟨oldContract, newContract, ?_⟩
  intro hRefines
  have hFalse : (true : Bool) = false :=
    hRefines.2 () ((), true) True.intro rfl
  cases hFalse

-- Equal endpoint snapshots can hide a transient authorization revocation
-- between observations. A time-continuity witness is an independent
-- premise; pairwise equality of point samples is not such a witness.
theorem endpoint_snapshots_do_not_prove_continuity :
    ∃ (trace : Fin 3 → Bool),
      trace 0 = trace 2 ∧ trace 1 ≠ trace 0 := by
  refine ⟨(fun t => if t = 1 then true else false), ?_, ?_⟩
  · decide
  · decide


-- A SECOND independent counterexample: the readset itself is correct, but
-- the change detector omitted a changed tracked source. A negative "no hit"
-- report cannot establish stable consumer behavior without changedCoversDelta.
theorem omitted_changed_source_invalidates_no_hit :
    ∃ (read changed : Bool → Prop) (oldEnv newEnv : Bool → Bool)
      (observe : (Bool → Bool) → Bool),
      ReadsetDetermines read observe ∧
      ¬ DirectlyAffected read changed ∧
      observe oldEnv ≠ observe newEnv := by
  refine ⟨(fun ref => ref = true), (fun ref => ref = false),
    (fun _ => false), (fun ref => ref), (fun env => env true), ?_, ?_, ?_⟩
  · intro oldEnv newEnv hAgreement
    exact hAgreement true rfl
  · intro hHit
    obtain ⟨ref, inRead, isChanged⟩ := hHit
    cases ref with
    | false => cases inRead
    | true => cases isChanged
  · decide

-- The admitted assumptions are not vacuous: disjoint source mutation
-- plus a complete property-specific readset permits reusing the *model*
-- consumer property without inspecting the mutated unrelated source.
theorem independent_config_change_preserves_model_property :
    let oldEnv : Bool → Bool := fun _ => false
    let newEnv : Bool → Bool := fun ref => if ref then false else true
    (fun env : Bool → Bool => env true) newEnv =
      (fun env : Bool → Bool => env true) oldEnv := by
  intro oldEnv newEnv
  have hFrame :
      ReadsetDetermines (fun ref : Bool => ref = true)
        (fun env : Bool → Bool => env true) := by
    intro before after agree
    exact agree true rfl
  have hCovers :
      ∀ ref : Bool, oldEnv ref ≠ newEnv ref → ref = false := by
    intro ref changed
    cases ref with
    | false => rfl
    | true => exact False.elim (changed rfl)
  have hNoHit :
      ¬ DirectlyAffected (fun ref : Bool => ref = true)
        (fun ref => ref = false) := by
    intro h
    obtain ⟨ref, inRead, changed⟩ := h
    cases ref with
    | false => cases inRead
    | true => cases changed
  exact property_scoped_reuse_if_frame_qualified
    (read := fun ref : Bool => ref = true)
    (changed := fun ref : Bool => ref = false)
    (oldEnv := oldEnv)
    (newEnv := newEnv)
    (observe := fun env : Bool → Bool => env true)
    (consumerProperty :=
      fun value => value = (fun env : Bool → Bool => env true) oldEnv)
    hFrame hCovers hNoHit rfl

-- Negative universal statements are themselves kernel-checked: omitting a
-- required frame or temporal condition is mathematically FALSE, not UNKNOWN.
theorem unqualified_frame_is_false :
    ¬ (∀ (read : Bool → Prop) (oldEnv newEnv : Bool → Bool)
        (observe : (Bool → Bool) → Bool),
        AgreesOn read oldEnv newEnv →
        observe oldEnv = observe newEnv) := by
  intro universal
  obtain ⟨read, oldEnv, newEnv, observe, hAgrees, hDiffers⟩ :=
    omitted_dependency_invalidates_unqualified_frame
  exact hDiffers (universal read oldEnv newEnv observe hAgrees)

theorem endpoint_equality_cannot_prove_full_time_continuity :
    ¬ (∀ (trace : Fin 3 → Bool), trace 0 = trace 2 →
       trace 1 = trace 0) := by
  intro universal
  obtain ⟨trace, hEndpoints, hMiddle⟩ :=
    endpoint_snapshots_do_not_prove_continuity
  exact hMiddle (universal trace hEndpoints)

end OrdivonR21
