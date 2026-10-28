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

-- A qualified negative-miss witness is a constructive frame condition:
-- every *unmarked* Ref has demonstrably equal values across the two worlds.
-- It is stronger as an evidence interface than treating caller-declared
-- 'no observed difference' as a full proof of readset closure.
theorem no_hit_implies_agreement
    {Ref Value : Type}
    (read changed : Ref → Prop)
    (oldEnv newEnv : Ref → Value)
    (unchangedIfNotMarked :
      ∀ ref, ¬ changed ref → oldEnv ref = newEnv ref)
    (noHit : ¬ DirectlyAffected read changed) :
    AgreesOn read oldEnv newEnv := by
  intro ref isRead
  apply unchangedIfNotMarked ref
  intro isChanged
  exact noHit ⟨ref, isRead, isChanged⟩

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
    (unchangedIfNotMarked :
      ∀ ref, ¬ changed ref → oldEnv ref = newEnv ref)
    (noHit : ¬ DirectlyAffected read changed)
    (oldProof : consumerProperty (observe oldEnv)) :
    consumerProperty (observe newEnv) := by
  have hAgree :=
    no_hit_implies_agreement read changed oldEnv newEnv unchangedIfNotMarked noHit
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
  refine ⟨(fun t : Fin 3 => match t.val with
    | 1 => true
    | _ => false), ?_, ?_⟩
  · rfl
  · intro impossible
    cases impossible


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
  have hNoFalseNegative :
      ∀ ref : Bool, ¬ ref = false → oldEnv ref = newEnv ref := by
    intro ref notMarked
    cases ref with
    | false => exact False.elim (notMarked rfl)
    | true => rfl
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
    hFrame hNoFalseNegative hNoHit rfl

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


-- FORMAL BRIDGE between the already-proved typed dependency graph and a
-- consumer-specific property frame. An edge is prerequisite -> consumer;
-- correctness of this graph against the ACTUAL implementation readset is an
-- explicit prerequisite, NOT inferred from path/Owner names or test PASS.
theorem graph_reuse_candidate_excludes_direct_readset_change
    {Ref : Type}
    (dependency : Ref → Ref → Prop)
    (changed unresolved read : Ref → Prop) (consumer : Ref)
    (readsHaveEdges : ∀ ref, read ref → dependency ref consumer)
    (candidate : StandsAt dependency changed unresolved consumer
      .reuseCandidate) :
    ¬ DirectlyAffected read (fun ref => changed ref ∨ unresolved ref) := by
  intro hHit
  obtain ⟨ref, hRead, hVariation⟩ := hHit
  have hEdge := readsHaveEdges ref hRead
  cases hVariation with
  | inl hChanged =>
      have reached : ImpactReach dependency changed consumer :=
        ImpactReach.successor ref consumer
          (ImpactReach.origin ref hChanged) hEdge
      exact candidate.1 reached
  | inr hUnresolved =>
      have reached : ImpactReach dependency unresolved consumer :=
        ImpactReach.successor ref consumer
          (ImpactReach.origin ref hUnresolved) hEdge
      exact candidate.2 reached

-- Under the required semantic implementation/refinement premises,
-- the (graph-only!) REUSE_CANDIDATE is sufficient for preserving a previously
-- proved, property-scoped mathematical goal. It is not domain acceptance or
-- an installed-program guarantee unless every premise is separately proved.
theorem graph_reuse_preserves_property_if_qualified
    {Ref Value Observation : Type}
    (dependency : Ref → Ref → Prop)
    (changed unresolved read : Ref → Prop) (consumer : Ref)
    (oldEnv newEnv : Ref → Value)
    (observe : (Ref → Value) → Observation)
    (consumerProperty : Observation → Prop)
    (readsHaveEdges : ∀ ref, read ref → dependency ref consumer)
    (readsetComplete : ReadsetDetermines read observe)
    (variationCoversDelta :
      ∀ ref, ¬ (changed ref ∨ unresolved ref) →
        oldEnv ref = newEnv ref)
    (candidate : StandsAt dependency changed unresolved consumer
      .reuseCandidate)
    (oldProof : consumerProperty (observe oldEnv)) :
    consumerProperty (observe newEnv) := by
  exact property_scoped_reuse_if_frame_qualified
    read (fun ref => changed ref ∨ unresolved ref)
    oldEnv newEnv observe consumerProperty
    readsetComplete variationCoversDelta
    (graph_reuse_candidate_excludes_direct_readset_change
      dependency changed unresolved read consumer readsHaveEdges candidate)
    oldProof

-- Constructive negative witness: the source change IS listed, the readset
-- IS correct, but the consumer edge is absent. The graph returns a reuse
-- candidate anyway while the actual observable flips. Thus a proof about
-- reachable declared nodes cannot prove real read-edge coverage.
theorem missing_consumer_edge_invalidates_graph_reuse :
    ∃ (dependency : Bool → Bool → Prop)
      (changed unresolved read : Bool → Prop)
      (consumer : Bool)
      (oldEnv newEnv : Bool → Bool)
      (observe : (Bool → Bool) → Bool),
      StandsAt dependency changed unresolved consumer .reuseCandidate ∧
      ReadsetDetermines read observe ∧
      (∀ ref, ¬ (changed ref ∨ unresolved ref) →
        oldEnv ref = newEnv ref) ∧
      observe oldEnv ≠ observe newEnv := by
  refine ⟨(fun _ _ => False), (fun ref => ref = true),
    (fun _ => False), (fun ref => ref = true), false,
    (fun _ => false), (fun ref => ref),
    (fun env => env true), ?_, ?_, ?_, ?_⟩
  · constructor
    · intro hReach
      cases hReach with
      | origin _ hChanged => cases hChanged
      | successor _ _ _ hEdge => exact False.elim hEdge
    · intro hReach
      cases hReach with
      | origin _ hUnresolved => exact False.elim hUnresolved
      | successor _ _ _ hEdge => exact False.elim hEdge
  · intro before after hAgree
    exact hAgree true rfl
  · intro ref noVariation
    cases ref with
    | false => rfl
    | true => exact False.elim (noVariation (Or.inl rfl))
  · decide

-- R2.1 successor-evaluation *necessary* source identity condition.
-- An external-to-candidate label cannot coexist with an anchor whose
-- declared controlling owner is the very candidate under evaluation.
-- This predicate does NOT establish authenticated external independence:
-- a second distinct string can still be a forged or candidate-controlled
-- identity; owner attestation and domain semantics remain UNKNOWN.
def ExternalAnchorIdentityConsistent {Identity : Type}
    (candidate owner : Identity) (claimedExternal : Prop) : Prop :=
  claimedExternal → owner ≠ candidate

theorem declared_external_anchor_cannot_be_self_owned {Identity : Type}
    (candidate owner : Identity)
    (hConsistent : ExternalAnchorIdentityConsistent candidate owner True) :
    owner ≠ candidate :=
  hConsistent True.intro

theorem self_owned_external_anchor_is_inconsistent {Identity : Type}
    (candidate : Identity) :
    ¬ ExternalAnchorIdentityConsistent candidate candidate True := by
  intro hQualified
  exact (hQualified True.intro) rfl

-- Independent negative witness: accepting the external relation label alone
-- for every identity is false. At least one owner/candidate alias makes it
-- logically impossible to claim independence on that exact identity basis.
theorem relation_label_alone_cannot_certify_external_identity :
    ¬ (∀ (candidate owner : Bool), ExternalAnchorIdentityConsistent candidate owner True) := by
  intro h
  exact self_owned_external_anchor_is_inconsistent true (h true true)

end OrdivonR21

#print axioms OrdivonR21.graph_reuse_candidate_excludes_direct_readset_change
#print axioms OrdivonR21.graph_reuse_preserves_property_if_qualified
#print axioms OrdivonR21.missing_consumer_edge_invalidates_graph_reuse

#print axioms OrdivonR21.declared_external_anchor_cannot_be_self_owned
#print axioms OrdivonR21.self_owned_external_anchor_is_inconsistent
#print axioms OrdivonR21.relation_label_alone_cannot_certify_external_identity
