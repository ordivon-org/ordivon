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

-- R2.1 scoped changed-source completeness is a set obligation, independent
-- of queue task selection. Observed source paths are a subset of real Git
-- changes; when source membership is decidable, no missing source is exactly
-- the condition needed to call the scope complete. This theorem does NOT
-- qualify whether the Python/Git producer discovered the *actual* paths.
theorem scoped_git_complete_iff_no_unobserved
    {Path : Type} (changed observed : Path → Prop)
    (observedIsChanged : ∀ path, observed path → changed path)
    (decObserved : ∀ path, Decidable (observed path)) :
    (∀ path, changed path ↔ observed path) ↔
      ¬ ∃ path, changed path ∧ ¬ observed path := by
  constructor
  · intro complete ⟨path, isChanged, isMissing⟩
    exact isMissing ((complete path).mp isChanged)
  · intro noMissing path
    constructor
    · intro isChanged
      letI := decObserved path
      by_cases isObserved : observed path
      · exact isObserved
      · exact False.elim (noMissing ⟨path, isChanged, isObserved⟩)
    · exact observedIsChanged path

-- Two genuinely changed paths may map to the SAME mandatory task. The
-- selected task image can therefore be identical even if an entire changed
-- source path has been omitted. Comparing task lists is NOT a lawful bridge
-- from task-set equality to SourceCut membership completeness.
theorem equal_task_images_can_hide_unobserved_git_source :
    ∃ (changed observed : Bool → Prop) (task : Bool → Bool),
      (∀ path, observed path → changed path) ∧
      (∀ t : Bool,
        (∃ path, changed path ∧ task path = t) ↔
        (∃ path, observed path ∧ task path = t)) ∧
      (∃ path, changed path ∧ ¬ observed path) := by
  refine ⟨(fun _ => True), (fun path => path = false),
    (fun _ => true), ?_, ?_, ?_⟩
  · intro path _
    trivial
  · decide
  · refine ⟨true, True.intro, ?_⟩
    decide

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

-- R2.1 original-repository history closure: Git ancestry may be checked on
-- a shallow repository which suppresses real parent edges. A positive path
-- witnessed in the partial graph remains a positive path in the complete
-- graph; a negative result is NOT a certificate of non-ancestry. This
-- distinction affects historical evidence admission and proof currentness.
--
-- NOTE: this is only an abstract graph-contract theorem. It does NOT show
-- that the actual Git objects, source repository identity, immutable import
-- bytes, or current implementation were qualified by the Python verifier.
inductive GitParentReach {Commit : Type}
    (parent : Commit → Commit → Prop) : Commit → Commit → Prop
  | refl (commit : Commit) : GitParentReach parent commit commit
  | step {older middle newer : Commit} :
      GitParentReach parent older middle →
      parent middle newer →
      GitParentReach parent older newer

theorem observed_git_ancestor_implies_actual
    {Commit : Type} (actual observed : Commit → Commit → Prop)
    (observedSubset : ∀ a b, observed a b → actual a b)
    {older newer : Commit}
    (observedPath : GitParentReach observed older newer) :
    GitParentReach actual older newer := by
  induction observedPath with
  | refl =>
      exact GitParentReach.refl _
  | step previous edge ih =>
      exact GitParentReach.step ih (observedSubset _ _ edge)

theorem complete_git_edges_transfer_actual_ancestry
    {Commit : Type} (actual observed : Commit → Commit → Prop)
    (actualCovered : ∀ a b, actual a b → observed a b)
    {older newer : Commit}
    (actualPath : GitParentReach actual older newer) :
    GitParentReach observed older newer := by
  exact observed_git_ancestor_implies_actual observed actual
    actualCovered actualPath

theorem empty_git_parent_edges_only_refl
    {Commit : Type} {older newer : Commit}
    (path : GitParentReach (fun _ _ => False) older newer) :
    older = newer := by
  induction path with
  | refl => rfl
  | step _ edge _ => exact False.elim edge

-- Non-vacuous countermodel: the complete graph has one real parent link
-- false -> true, the shallow graph sees no links, and therefore reports a
-- negative ancestry relation which is false in the full graph.
theorem shallow_git_non_ancestor_is_not_authoritative :
    ∃ (actual observed : Bool → Bool → Prop),
      (∀ a b, observed a b → actual a b) ∧
      GitParentReach actual false true ∧
      ¬ GitParentReach observed false true := by
  refine ⟨(fun a b => a = false ∧ b = true),
    (fun _ _ => False), ?_, ?_, ?_⟩
  · intro _ _ h
    exact False.elim h
  · exact GitParentReach.step (GitParentReach.refl false) ⟨rfl, rfl⟩
  · intro shallowPath
    exact (by decide : false ≠ true)
      (empty_git_parent_edges_only_refl shallowPath)

-- Distinguish a proven negative ancestor answer from merely having no
-- observable path: a negative answer transfers ONLY if the necessary
-- complete-history/parent-edge inclusion premise was discharged.
theorem qualified_git_non_ancestor_if_complete
    {Commit : Type} (actual observed : Commit → Commit → Prop)
    (actualCovered : ∀ a b, actual a b → observed a b)
    {older newer : Commit}
    (noObservedPath : ¬ GitParentReach observed older newer) :
    ¬ GitParentReach actual older newer := by
  intro actualPath
  exact noObservedPath
    (complete_git_edges_transfer_actual_ancestry actual observed
      actualCovered actualPath)

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

#print axioms OrdivonR21.observed_git_ancestor_implies_actual
#print axioms OrdivonR21.shallow_git_non_ancestor_is_not_authoritative
#print axioms OrdivonR21.qualified_git_non_ancestor_if_complete
#print axioms OrdivonR21.scoped_git_complete_iff_no_unobserved
#print axioms OrdivonR21.equal_task_images_can_hide_unobserved_git_source
#print axioms OrdivonR21.graph_reuse_candidate_excludes_direct_readset_change
#print axioms OrdivonR21.graph_reuse_preserves_property_if_qualified
#print axioms OrdivonR21.missing_consumer_edge_invalidates_graph_reuse

#print axioms OrdivonR21.declared_external_anchor_cannot_be_self_owned
#print axioms OrdivonR21.self_owned_external_anchor_is_inconsistent
#print axioms OrdivonR21.relation_label_alone_cannot_certify_external_identity


-- Restricted communication core LEGO: every "reply_to" edge must point to
-- an already committed, earlier Host Message sequence.  It does not constrain
-- "references", "about", or other graph relations.
-- Full R2.1 ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold):
-- id=host.message.reply-chronology; responsibility=acyclic causal reply graph;
-- I=(sourceRef,targetRef,sourceOrdinal,targetOrdinal), O=admitted/rejected;
-- S=immutable-message ordinal map plus reply-only edge relation;
-- pre=both message refs exist, same topic, and ordinals are immutable;
-- post=permit edge iff targetOrdinal < sourceOrdinal;
-- inv=all admitted reply-only edges descend in ordinal, graph is acyclic;
-- eff=one directed reply relation append or none, not external IO authority;
-- c=one integer comparison model; concrete DB cost UNKNOWN;
-- epsilon=0 exact Nat order, prov=this kernel term/Host sourcecut;
-- unfold=existing Host message + relation API and PostgreSQL ordinal owner;
-- acceptance=kernel checked path descent/no cycle and unchecked countermodel.
-- This is a mathematical model, NOT automatic implementation refinement of
-- Python/psycopg or a claim that PostgreSQL commits by sequence order.
namespace OrdivonR21.CausalReply

def Qualified {Ref : Type} (ordinal : Ref → Nat)
    (reply : Ref → Ref → Prop) : Prop :=
  ∀ source target, reply source target → ordinal target < ordinal source

theorem causal_chain_descends {Ref : Type}
    (ordinal : Ref → Nat) (reply : Ref → Ref → Prop)
    (hQualified : Qualified ordinal reply)
    {source target : Ref} (hPath : Relation.TransGen reply source target) :
    ordinal target < ordinal source := by
  induction hPath with
  | single hEdge =>
      exact hQualified _ _ hEdge
  | tail hPrefix hFinal ih =>
      exact Nat.lt_trans (hQualified _ _ hFinal) ih

theorem qualified_reply_graph_acyclic {Ref : Type}
    (ordinal : Ref → Nat) (reply : Ref → Ref → Prop)
    (hQualified : Qualified ordinal reply) (source : Ref) :
    ¬ Relation.TransGen reply source source := by
  intro hCycle
  have hDescending : ordinal source < ordinal source :=
    causal_chain_descends ordinal reply hQualified hCycle
  exact (Nat.lt_irrefl _ hDescending)

theorem guarded_append_preserves_qualification {Ref : Type}
    (ordinal : Ref → Nat) (reply : Ref → Ref → Prop)
    (hQualified : Qualified ordinal reply)
    (source target : Ref) (hEarlier : ordinal target < ordinal source) :
    Qualified ordinal
      (fun a b => reply a b ∨ (a = source ∧ b = target)) := by
  intro a b edge
  rcases edge with hOld | ⟨ha, hb⟩
  · exact hQualified _ _ hOld
  · subst a
    subst b
    exact hEarlier

theorem unguarded_self_reply_is_cyclic :
    ∃ (reply : Bool → Bool → Prop),
      Relation.TransGen reply true true := by
  exact ⟨(fun a b => a = b), Relation.TransGen.single rfl⟩

-- Pure decision: Python checks target_sequence >= source_sequence
-- and raises ConflictError. This proves order semantics for Nat only;
-- SQL decoding and real Python control flow remain separate obligations.
def decision (sourceOrdinal targetOrdinal : Nat) : Bool :=
  decide (targetOrdinal < sourceOrdinal)

def decisionContract : OrdivonR21.IOContract (Nat × Nat) Bool where
  assume := fun _ => True
  guarantee := fun input output =>
    output = decision input.1 input.2

def decisionBehavior (input : Nat × Nat) (output : Bool) : Prop :=
  output = decision input.1 input.2

theorem decision_implements_model :
    OrdivonR21.Implements decisionContract decisionBehavior := by
  constructor
  · intro input output _ h
    exact h
  · intro input _
    exact ⟨decision input.1 input.2, rfl⟩

theorem python_rejection_predicate_iff_model_not_permitted
    (sourceOrdinal targetOrdinal : Nat) :
    (sourceOrdinal ≤ targetOrdinal) ↔
      decision sourceOrdinal targetOrdinal = false := by
  simp [decision, decide_eq_false_iff_not]

theorem reversed_message_pair_rejected :
    ¬ (1 < (0 : Nat)) := by
  decide

end OrdivonR21.CausalReply

#print axioms OrdivonR21.CausalReply.causal_chain_descends
#print axioms OrdivonR21.CausalReply.qualified_reply_graph_acyclic
#print axioms OrdivonR21.CausalReply.guarded_append_preserves_qualification
#print axioms OrdivonR21.CausalReply.unguarded_self_reply_is_cyclic
#print axioms OrdivonR21.CausalReply.decision_implements_model
#print axioms OrdivonR21.CausalReply.python_rejection_predicate_iff_model_not_permitted
