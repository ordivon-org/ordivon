-- Restricted R2.1 relational composition; not an installed-code refinement.
theorem r21_assume_guarantee_refinement {α : Type}
    (P Q : α → Prop) (h : ∀ x, P x → Q x)
    (x : α) (hp : P x) : Q x :=
  h x hp

theorem r21_seq_relation_monotone {α β γ : Type}
    (R R' : α → β → Prop) (S : β → γ → Prop)
    (h : ∀ x y, R' x y → R x y) :
    ∀ x z, (∃ y, R' x y ∧ S y z) → ∃ y, R x y ∧ S y z := by
  intro x z ⟨y, hr, hs⟩
  exact ⟨y, h x y hr, hs⟩


-- A task-scoped input/output profile of the canonical R2.1 contract.
-- No new universal calculus is introduced. Here the accepted-input
-- totality clause excludes the empty-relation/vacuous-safety failure.
namespace OrdivonR21

structure IOContract (α β : Type) where
  assume : α → Prop
  guarantee : α → β → Prop

def Implements {α β : Type} (C : IOContract α β)
    (behavior : α → β → Prop) : Prop :=
  (∀ x y, C.assume x → behavior x y → C.guarantee x y) ∧
  (∀ x, C.assume x → ∃ y, behavior x y)

def Refines {α β : Type}
    (new old : IOContract α β) : Prop :=
  (∀ x, old.assume x → new.assume x) ∧
  (∀ x y, old.assume x → new.guarantee x y → old.guarantee x y)

-- R2.1 behavioral contract semantics adopted from standard saturated
-- assume/guarantee algebra. The pair (x,y) denotes one *consumer-observable*
-- input/output behavior. Restricted to the SAME α and β: no port adapter,
-- effect projection or installed equivalence follows from type alignment.
def SaturatedGuarantee {α β : Type}
    (C : IOContract α β) (x : α) (y : β) : Prop :=
  ¬ C.assume x ∨ C.guarantee x y

-- Safety satisfaction and admissible-input totality are distinct R2.1
-- obligations. Saturation cannot make an output-free implementation total.
theorem safety_satisfaction_iff_saturated {α β : Type}
    (C : IOContract α β) (behavior : α → β → Prop)
    (decidableAssume : ∀ x, Decidable (C.assume x)) :
    (∀ x y, C.assume x → behavior x y → C.guarantee x y) ↔
    (∀ x y, behavior x y → SaturatedGuarantee C x y) := by
  constructor
  · intro h x y hBehavior
    letI : Decidable (C.assume x) := decidableAssume x
    by_cases hA : C.assume x
    · exact Or.inr (h x y hA hBehavior)
    · exact Or.inl hA
  · intro h x y hA hBehavior
    rcases h x y hBehavior with hNot | hG
    · exact False.elim (hNot hA)
    · exact hG

-- R2.1 Refines is precisely the same-port saturated contract preorder.
-- This theorem connects the existing executable formal carrier to the
-- project's canonical contract algebra, not to any external real consumer.
theorem refinement_iff_saturated_guarantee {α β : Type}
    (new old : IOContract α β)
    (decidableOldAssume : ∀ x, Decidable (old.assume x)) :
    Refines new old ↔
      (∀ x, old.assume x → new.assume x) ∧
      (∀ x y, SaturatedGuarantee new x y →
        SaturatedGuarantee old x y) := by
  constructor
  · intro h
    constructor
    · exact h.1
    · intro x y hSat
      letI : Decidable (old.assume x) := decidableOldAssume x
      by_cases hOld : old.assume x
      · rcases hSat with hNotNew | hGNew
        · exact False.elim (hNotNew (h.1 x hOld))
        · exact Or.inr (h.2 x y hOld hGNew)
      · exact Or.inl hOld
  · intro h
    constructor
    · exact h.1
    · intro x y hOld hGNew
      rcases h.2 x y (Or.inr hGNew) with hNotOld | hGOld
      · exact False.elim (hNotOld hOld)
      · exact hGOld

-- Negative finite witness: the new component accepts only true whereas
-- the old consumer may send false. Equal output guarantees cannot rescue
-- an implementation that excludes a previously admitted input.
theorem narrowed_assumptions_cannot_substitute :
    ∃ (old new : IOContract Bool Unit),
      (∀ x y, new.guarantee x y ↔ old.guarantee x y) ∧
      ¬ Refines new old := by
  let old : IOContract Bool Unit := {
    assume := fun _ => True
    guarantee := fun _ _ => True
  }
  let new : IOContract Bool Unit := {
    assume := fun value => value = true
    guarantee := fun _ _ => True
  }
  refine ⟨old, new, ?_, ?_⟩
  · intro _ _
    exact Iff.rfl
  · intro hRef
    have hNarrow : (false : Bool) = true := hRef.1 false True.intro
    cases hNarrow

theorem refinement_preserves_implementation {α β : Type}
    (new old : IOContract α β) (behavior : α → β → Prop)
    (hImpl : Implements new behavior) (hRef : Refines new old) :
    Implements old behavior := by
  constructor
  · intro x y hOldA hBehavior
    have hNewA : new.assume x := hRef.1 x hOldA
    exact hRef.2 x y hOldA (hImpl.1 x y hNewA hBehavior)
  · intro x hOldA
    exact hImpl.2 x (hRef.1 x hOldA)

-- The negative case is mechanically PROVED, not merely hand-waved:
-- a purely safety-based requirement would accept a component with no output.
theorem vacuous_safety_is_not_total :
    ∃ (R : Unit → Unit → Prop),
      (∀ x y, R x y → True) ∧ ¬ (∀ x, ∃ y, R x y) := by
  refine ⟨(fun _ _ => False), ?_, ?_⟩
  · intro _ _ h
    exact False.elim h
  · intro h
    exact (h ()).elim (fun _ hf => hf)


-- Existing R2.1 contracts compose only when the first component's
-- output guarantee discharges the second component's input assumption.
-- This is a standard assume–guarantee compatibility obligation.
def sequentialContract {α β γ : Type}
    (first : IOContract α β) (second : IOContract β γ) :
    IOContract α γ where
  assume := first.assume
  guarantee := fun x z =>
    ∃ y, first.guarantee x y ∧ second.guarantee y z

def sequentialBehavior {α β γ : Type}
    (R : α → β → Prop) (S : β → γ → Prop) : α → γ → Prop :=
  fun x z => ∃ y, R x y ∧ S y z

theorem sequential_implements_if_compatible {α β γ : Type}
    (first : IOContract α β) (second : IOContract β γ)
    (R : α → β → Prop) (S : β → γ → Prop)
    (hFirst : Implements first R) (hSecond : Implements second S)
    (compatible : ∀ x y, first.assume x →
      first.guarantee x y → second.assume y) :
    Implements (sequentialContract first second)
      (sequentialBehavior R S) := by
  constructor
  · intro x z hA ⟨y, hR, hS⟩
    have hG1 := hFirst.1 x y hA hR
    exact ⟨y, hG1, hSecond.1 y z (compatible x y hA hG1) hS⟩
  · intro x hA
    obtain ⟨y, hR⟩ := hFirst.2 x hA
    have hG1 := hFirst.1 x y hA hR
    obtain ⟨z, hS⟩ := hSecond.2 y (compatible x y hA hG1)
    exact ⟨z, y, hR, hS⟩

-- Nonvacuity: two implementations can each satisfy their own contracts,
-- yet their sequential composition is not total when assumptions conflict.
theorem incompatible_components_are_not_composable :
    ∃ (first : IOContract Unit Bool) (second : IOContract Bool Unit)
      (R : Unit → Bool → Prop) (S : Bool → Unit → Prop),
      Implements first R ∧ Implements second S ∧
      ¬ Implements (sequentialContract first second)
          (sequentialBehavior R S) := by
  let first : IOContract Unit Bool := {
    assume := fun _ => True
    guarantee := fun _ b => b = true
  }
  let second : IOContract Bool Unit := {
    assume := fun b => b = false
    guarantee := fun _ _ => True
  }
  let R : Unit → Bool → Prop := fun _ b => b = true
  let S : Bool → Unit → Prop := fun b _ => b = false
  refine ⟨first, second, R, S, ?_, ?_, ?_⟩
  · constructor
    · intro _ _ _ h
      exact h
    · intro _ _
      exact ⟨true, rfl⟩
  · constructor
    · intro _ _ _ _
      trivial
    · intro b hb
      exact ⟨(), hb⟩
  · intro h
    obtain ⟨_, y, hR, hS⟩ := h.2 () trivial
    have ht : y = true := hR
    have hf : y = false := hS
    simp [ht] at hf


-- Proof/readset incrementality is a *conditional* theorem. The proposition
-- depends only on a projection if equal projections make its truth invariant.
-- This obligation is not established merely by Git object identity.
def DependsOnlyOn {α ρ : Type} (readset : α → ρ)
    (goal : α → Prop) : Prop :=
  ∀ before after, readset before = readset after →
    (goal before ↔ goal after)

theorem reuse_if_readset_covers_goal {α ρ : Type}
    (readset : α → ρ) (goal : α → Prop)
    (hClosed : DependsOnlyOn readset goal)
    (before after : α)
    (hSame : readset before = readset after)
    (hVerified : goal before) : goal after :=
  (hClosed before after hSame).mp hVerified

-- Adding a needed dependency to the readset cannot weaken soundness.
-- The reverse (discarding dependencies) is NOT generally valid.
theorem extending_qualified_readset_preserves_soundness {α ρ δ : Type}
    (readset : α → ρ) (extra : α → δ) (goal : α → Prop)
    (hClosed : DependsOnlyOn readset goal) :
    DependsOnlyOn (fun x => (readset x, extra x)) goal := by
  intro before after hPair
  exact hClosed before after (congrArg Prod.fst hPair)

-- Concrete independent counterexample: the immutable *source* input agrees
-- while an environmental assumption (including a dynamic consumer, plugin,
-- permission or installed dependency) changes, reversing a required goal.
structure SourceEnvironment (σ ε : Type) where
  source : σ
  environment : ε

def environmentGoal (s : SourceEnvironment Unit Bool) : Prop :=
  s.environment = true

theorem source_only_readset_is_not_complete :
    ¬ DependsOnlyOn
      (fun s : SourceEnvironment Unit Bool => s.source)
      environmentGoal := by
  intro hClosed
  have hOld : environmentGoal ⟨(), true⟩ := rfl
  have hNew : environmentGoal ⟨(), false⟩ :=
    (hClosed ⟨(), true⟩ ⟨(), false⟩ rfl).mp hOld
  simp [environmentGoal] at hNew

-- In this bounded two-field model, an explicit source+environment readset
-- is complete for this goal. This is NOT a proof of real-world dependency
-- closure, toolchain identity, installed currentness or actual code refinement.
theorem source_and_environment_readset_is_complete :
    DependsOnlyOn
      (fun s : SourceEnvironment Unit Bool => (s.source, s.environment))
      environmentGoal := by
  intro before after hInput
  have hEnv : before.environment = after.environment := by
    simpa only using (congrArg Prod.snd hInput)
  change (before.environment = true ↔ after.environment = true)
  constructor
  · intro hBefore
    rw [← hEnv]
    exact hBefore
  · intro hAfter
    rw [hEnv]
    exact hAfter

end OrdivonR21

-- Incremental reasoning requires a CLOSED actual dependency scope, not an
-- Owner label, source-path lookup, unchanged Git blob, or a caller's guess.
-- This is a conditional frame rule for pure, deterministic observations.
-- Real effectful/non-deterministic systems need a separately proved trace
-- and environment refinement satisfying the explicit extensional premise.
namespace OrdivonR21

def DependencyClosed {δ : Type}
    (declared actual : δ → Prop) : Prop :=
  ∀ d, actual d → declared d

def StableWithin {δ β : Type}
    (declared : δ → Prop) (before after : δ → β) : Prop :=
  ∀ d, declared d → before d = after d

def ObservableDependsOnlyOn {δ β γ : Type}
    (actual : δ → Prop) (observable : (δ → β) → γ) : Prop :=
  ∀ before after,
    (∀ d, actual d → before d = after d) →
    observable before = observable after

-- A sound frame conclusion is available ONLY after independently justifying
-- each premise, including the closure and the implementation's dependency
-- extensionality. No Agent or Repo Owner identity occurs in the theorem.
theorem closed_dependency_frame {δ β γ : Type}
    (declared actual : δ → Prop)
    (before after : δ → β) (observable : (δ → β) → γ)
    (hClosed : DependencyClosed declared actual)
    (hStable : StableWithin declared before after)
    (hObserves : ObservableDependsOnlyOn actual observable) :
    observable before = observable after := by
  apply hObserves before after
  intro d hActual
  exact hStable d (hClosed d hActual)

-- Counterexample: both source states coincide at EVERY declared dependency,
-- but a hidden (real) dependency differs, and an actual observable changes.
-- Therefore "declared scope unchanged" alone cannot justify a reuse PASS.
theorem unlisted_dependency_breaks_frame :
    ∃ (declared actual : Bool → Prop)
      (before after : Bool → Bool)
      (observable : (Bool → Bool) → Bool),
      StableWithin declared before after ∧
      ObservableDependsOnlyOn actual observable ∧
      ¬ DependencyClosed declared actual ∧
      observable before ≠ observable after := by
  refine ⟨(fun d => d = false), (fun d => d = true),
    (fun _ => false), (fun d => d),
    (fun values => values true), ?_, ?_, ?_, ?_⟩
  · intro d hd
    cases d with
    | false => rfl
    | true => cases hd
  · intro old new hSame
    exact hSame true rfl
  · intro hClosed
    have hImpossible : true = false := hClosed true rfl
    cases hImpossible
  · decide

-- A SOURCE/API-only equivalence cannot justify LEGO replacement when
-- environment-visible effects or authority outcomes differ.  This theorem
-- instantiates the existing IOContract with (public output, observable effect)
-- rather than creating another module calculus or assuming an Agent Owner.
-- The candidates are total and have identical public output projections.
theorem equal_public_outputs_do_not_prove_effect_substitution :
    ∃ (spec : IOContract Unit (Unit × Bool))
      (original candidate : Unit → (Unit × Bool) → Prop),
      Implements spec original ∧
      (∀ inp out,
        (∃ effect : Bool, original inp (out, effect)) ↔
        (∃ effect : Bool, candidate inp (out, effect))) ∧
      ¬ Implements spec candidate := by
  let spec : IOContract Unit (Unit × Bool) := {
    assume := fun _ => True
    guarantee := fun _ result => result.2 = false
  }
  let original : Unit → (Unit × Bool) → Prop :=
    fun _ result => result.2 = false
  let candidate : Unit → (Unit × Bool) → Prop :=
    fun _ result => result.2 = true
  refine ⟨spec, original, candidate, ?_, ?_, ?_⟩
  · constructor
    · intro _ result _ hOriginal
      exact hOriginal
    · intro _ _
      exact ⟨((), false), rfl⟩
  · intro inp out
    constructor
    · intro _
      exact ⟨true, rfl⟩
    · intro _
      exact ⟨false, rfl⟩
  · intro hCandidate
    have hContradiction : true = false :=
      hCandidate.1 () ((), true) True.intro rfl
    cases hContradiction

-- This countermodel disproves the inference
-- "same public I/O projection => effect/authority-preserving replacement".
-- It does NOT assert that any particular Gateway or Runtime implementation
-- violates its contract: that requires separate model-to-code refinement.

end OrdivonR21

#print axioms OrdivonR21.closed_dependency_frame
#print axioms OrdivonR21.unlisted_dependency_breaks_frame

-- The source-only Agent transport projection can OMIT only declared misses.
-- This small standard List.filter law is separate from dependency-frame
-- soundness: it is NOT permission to reuse an implementation proof.
namespace OrdivonR21

inductive SourceImpactStanding where
  | noDeclaredHit
  | unknown
  | recheckRequired
  | changed
  deriving DecidableEq, Repr

def CompactImpact (rows : List SourceImpactStanding) :
    List SourceImpactStanding :=
  rows.filter (fun standing => standing != .noDeclaredHit)

theorem agent_impact_preserves_nontrivial_standings
    (rows : List SourceImpactStanding) (standing : SourceImpactStanding) :
    standing ∈ CompactImpact rows ↔
      standing ∈ rows ∧ standing ≠ .noDeclaredHit := by
  simp [CompactImpact]

theorem agent_impact_cannot_hide_unknown
    (rows : List SourceImpactStanding)
    (h : SourceImpactStanding.unknown ∈ rows) :
    SourceImpactStanding.unknown ∈ CompactImpact rows := by
  exact (agent_impact_preserves_nontrivial_standings rows
    .unknown).2 ⟨h, by decide⟩

theorem agent_impact_cannot_hide_recheck
    (rows : List SourceImpactStanding)
    (h : SourceImpactStanding.recheckRequired ∈ rows) :
    SourceImpactStanding.recheckRequired ∈ CompactImpact rows := by
  exact (agent_impact_preserves_nontrivial_standings rows
    .recheckRequired).2 ⟨h, by decide⟩

theorem agent_impact_excludes_declared_misses
    (rows : List SourceImpactStanding) :
    SourceImpactStanding.noDeclaredHit ∉ CompactImpact rows := by
  intro h
  exact ((agent_impact_preserves_nontrivial_standings rows
    .noDeclaredHit).1 h).2 rfl

end OrdivonR21

#print axioms OrdivonR21.agent_impact_preserves_nontrivial_standings
#print axioms OrdivonR21.agent_impact_cannot_hide_unknown
#print axioms OrdivonR21.agent_impact_cannot_hide_recheck
#print axioms OrdivonR21.agent_impact_excludes_declared_misses

#print axioms OrdivonR21.reuse_if_readset_covers_goal
#print axioms OrdivonR21.extending_qualified_readset_preserves_soundness

-- R2.1 incremental selector's task-local *priority* semantics.
-- This is deliberately separate from the real Python worklist: theorem
-- validity does not establish Python implementation refinement.
-- A rank is one of 0=REUSE_CANDIDATE, 1=UNKNOWN, 2=RECHECK_REQUIRED.
-- Dependency edges point from consumer to prerequisite.
namespace OrdivonR21.PriorityClosure

universe u
variable {Node : Type u}

inductive Demand (base : Node → Nat)
    (edges : Node → Node → Prop) : Node → Nat → Prop where
  | seed {node threshold} (h : threshold ≤ base node) :
      Demand base edges node threshold
  | consumer {node prerequisite threshold}
      (edge : edges node prerequisite)
      (need : Demand base edges prerequisite threshold) :
      Demand base edges node threshold

-- Every derived priority must be below ANY proposed post-state assignment
-- satisfying the seed and consumer-edge obligations; therefore no smaller
-- closed status assignment can discard a justified change/unknown.
theorem least_closed_priority
    (base : Node → Nat) (edges : Node → Node → Prop)
    (candidate : Node → Nat)
    (seedBound : ∀ node, base node ≤ candidate node)
    (edgeBound : ∀ node prerequisite,
      edges node prerequisite →
      candidate prerequisite ≤ candidate node)
    {node threshold} (proof : Demand base edges node threshold) :
    threshold ≤ candidate node := by
  induction proof with
  | seed h =>
      exact Nat.le_trans h (seedBound _)
  | consumer edge _ ih =>
      exact Nat.le_trans ih (edgeBound _ _ edge)

-- The inductive closure is the *least* relation containing the local seeds
-- and closed under the existing directed consumer/prerequisite relation.
theorem demand_least_inductive_closure
    (base : Node → Nat) (edges : Node → Node → Prop)
    (closed : Node → Nat → Prop)
    (seed : ∀ node threshold, threshold ≤ base node → closed node threshold)
    (step : ∀ node prerequisite threshold,
      edges node prerequisite →
      closed prerequisite threshold → closed node threshold)
    {node threshold} (proof : Demand base edges node threshold) :
    closed node threshold := by
  induction proof with
  | seed h => exact seed _ _ h
  | consumer edge _ ih => exact step _ _ _ edge ih

-- More local evidence or additional consumer edges may raise, never lower,
-- the mathematical demand closure. In particular RECHECK(2) dominates
-- UNKNOWN(1) independent of queue ordering.
theorem demand_monotone
    (before after : Node → Nat)
    (oldEdges newEdges : Node → Node → Prop)
    (moreSeeds : ∀ node, before node ≤ after node)
    (moreEdges : ∀ node prerequisite,
      oldEdges node prerequisite → newEdges node prerequisite)
    {node threshold}
    (proof : Demand before oldEdges node threshold) :
    Demand after newEdges node threshold := by
  induction proof with
  | seed h =>
      exact Demand.seed (Nat.le_trans h (moreSeeds _))
  | consumer edge _ ih =>
      exact Demand.consumer (moreEdges _ _ edge) ih

-- A priority-2 change also witnesses priority-1; the selector's explicit
-- RECHECK > UNKNOWN decision must keep the stronger established demand.
theorem demand_is_downward_closed
    (base : Node → Nat) (edges : Node → Node → Prop)
    {node high low} (hThreshold : low ≤ high)
    (proof : Demand base edges node high) :
    Demand base edges node low := by
  induction proof with
  | seed h =>
      exact Demand.seed (Nat.le_trans hThreshold h)
  | consumer edge _ ih =>
      exact Demand.consumer edge (ih hThreshold)

def RecheckDemand (base : Node → Nat)
    (edges : Node → Node → Prop) (node : Node) : Prop :=
  Demand base edges node 2

def UnknownOnlyDemand (base : Node → Nat)
    (edges : Node → Node → Prop) (node : Node) : Prop :=
  Demand base edges node 1 ∧ ¬ RecheckDemand base edges node

def ReuseCandidateDemand (base : Node → Nat)
    (edges : Node → Node → Prop) (node : Node) : Prop :=
  ¬ Demand base edges node 1 ∧ ¬ RecheckDemand base edges node

theorem recheck_supersedes_unknown
    (base : Node → Nat) (edges : Node → Node → Prop)
    {node} (h : RecheckDemand base edges node) :
    Demand base edges node 1 ∧ ¬ UnknownOnlyDemand base edges node := by
  constructor
  · exact demand_is_downward_closed base edges (by decide) h
  · intro hUnknown
    exact hUnknown.2 h

theorem unknown_only_not_reuse
    (base : Node → Nat) (edges : Node → Node → Prop)
    {node} (h : UnknownOnlyDemand base edges node) :
    ¬ ReuseCandidateDemand base edges node := by
  intro hReuse
  exact hReuse.1 h.1

-- A claimed owner/agent approval has no input to Demand or its closure.
-- It is a mathematical *candidate* selector, never a proof-reuse certificate.
end OrdivonR21.PriorityClosure

#print axioms OrdivonR21.PriorityClosure.least_closed_priority
#print axioms OrdivonR21.PriorityClosure.demand_least_inductive_closure
#print axioms OrdivonR21.PriorityClosure.demand_monotone
#print axioms OrdivonR21.PriorityClosure.demand_is_downward_closed
#print axioms OrdivonR21.PriorityClosure.recheck_supersedes_unknown
#print axioms OrdivonR21.PriorityClosure.unknown_only_not_reuse


-- Task-local dependency impact calculus, separate from physical source/install truth.
-- The direction is prerequisite -> consumer: a changed prerequisite affects the
-- downstream consumer; unrelated components are not poisoned without a path.
-- This is a logical model of Composition.select_impacted_obligations, NOT a
-- mechanized refinement of its Python worklist, nor proof of readset closure.
namespace OrdivonR21

inductive ImpactReach {α : Type}
    (dependency : α → α → Prop) (roots : α → Prop) : α → Prop where
  | origin (x : α) : roots x → ImpactReach dependency roots x
  | successor (upstream downstream : α) :
      ImpactReach dependency roots upstream →
      dependency upstream downstream →
      ImpactReach dependency roots downstream

-- Sound scheduling must include every changed root and every downstream node.
theorem impact_includes_changed {α : Type}
    (dependency : α → α → Prop) (changed : α → Prop)
    (x : α) (h : changed x) :
    ImpactReach dependency changed x :=
  ImpactReach.origin x h

theorem impact_includes_consumer {α : Type}
    (dependency : α → α → Prop) (changed : α → Prop)
    (upstream downstream : α)
    (hu : ImpactReach dependency changed upstream)
    (hedge : dependency upstream downstream) :
    ImpactReach dependency changed downstream :=
  ImpactReach.successor upstream downstream hu hedge

-- Minimality: no smaller impact set can contain all roots and remain closed
-- under actual declared dependency edges.
theorem impact_least_forward_closed {α : Type}
    (dependency : α → α → Prop) (roots admissible : α → Prop)
    (hroot : ∀ x, roots x → admissible x)
    (hclosed : ∀ x y, admissible x → dependency x y → admissible y) :
    ∀ x, ImpactReach dependency roots x → admissible x := by
  intro x h
  induction h with
  | origin y hy => exact hroot y hy
  | successor a b _ hab ih => exact hclosed a b ih hab

-- An additional dependency never removes an already impacted consumer.
theorem impact_monotone_in_declared_edges {α : Type}
    (oldEdges newEdges : α → α → Prop) (roots : α → Prop)
    (hedge : ∀ x y, oldEdges x y → newEdges x y) :
    ∀ x, ImpactReach oldEdges roots x → ImpactReach newEdges roots x := by
  intro x h
  induction h with
  | origin y hy => exact ImpactReach.origin y hy
  | successor a b _ hab ih =>
      exact ImpactReach.successor a b ih (hedge a b hab)

-- The three-valued result distinguishes RECHECK, UNKNOWN and mere reuse
-- CANDIDATE. The logical status is not a verifier PASS or proof-admission.
inductive ImpactStanding where
  | reuseCandidate | unknown | recheck

def StandsAt {α : Type}
    (dependency : α → α → Prop)
    (changed unresolved : α → Prop) (x : α) :
    ImpactStanding → Prop
  | .recheck => ImpactReach dependency changed x
  | .unknown =>
      ¬ ImpactReach dependency changed x ∧
        ImpactReach dependency unresolved x
  | .reuseCandidate =>
      ¬ ImpactReach dependency changed x ∧
        ¬ ImpactReach dependency unresolved x

theorem changed_never_reuse_candidate {α : Type}
    (dependency : α → α → Prop)
    (changed unresolved : α → Prop)
    (x : α) (hc : ImpactReach dependency changed x) :
    ¬ StandsAt dependency changed unresolved x .reuseCandidate := by
  intro h
  exact h.1 hc

-- A hard change always dominates UNKNOWN on the same dependency branch.
theorem recheck_dominates_unknown {α : Type}
    (dependency : α → α → Prop)
    (changed unresolved : α → Prop)
    (x : α) (hc : ImpactReach dependency changed x) :
    StandsAt dependency changed unresolved x .recheck ∧
      ¬ StandsAt dependency changed unresolved x .unknown := by
  constructor
  · exact hc
  · intro h
    exact h.1 hc

theorem unknown_never_reuse_candidate {α : Type}
    (dependency : α → α → Prop)
    (changed unresolved : α → Prop)
    (x : α) (hu : ImpactReach dependency unresolved x) :
    ¬ StandsAt dependency changed unresolved x .reuseCandidate := by
  intro h
  exact h.2 hu

theorem unaffected_branch_is_reuse_candidate_not_proof {α : Type}
    (dependency : α → α → Prop)
    (changed unresolved : α → Prop)
    (x : α)
    (hc : ¬ ImpactReach dependency changed x)
    (hu : ¬ ImpactReach dependency unresolved x) :
    StandsAt dependency changed unresolved x .reuseCandidate :=
  ⟨hc, hu⟩

-- Closed finite negative oracle: with no edges, changing A does not impact B.
inductive DisjointLEGO where
  | a | b

def noDependency : DisjointLEGO → DisjointLEGO → Prop := fun _ _ => False

def changedA : DisjointLEGO → Prop := fun x => x = .a

theorem unrelated_lego_not_impacted :
    ¬ ImpactReach noDependency changedA DisjointLEGO.b := by
  intro h
  have hOnlyA : ∀ x, ImpactReach noDependency changedA x → x = .a := by
    intro x hx
    induction hx with
    | origin y hy => exact hy
    | successor _ _ _ edge _ => exact False.elim edge
  have contradiction : DisjointLEGO.b = DisjointLEGO.a := hOnlyA _ h
  cases contradiction

-- A real typed edge from A to B instead requires rechecking B.
def aToB : DisjointLEGO → DisjointLEGO → Prop :=
  fun upstream downstream => upstream = .a ∧ downstream = .b

theorem real_consumer_must_be_rechecked :
    ImpactReach aToB changedA DisjointLEGO.b := by
  apply ImpactReach.successor DisjointLEGO.a DisjointLEGO.b
  · exact ImpactReach.origin DisjointLEGO.a rfl
  · exact ⟨rfl, rfl⟩

end OrdivonR21

#print axioms OrdivonR21.impact_least_forward_closed
#print axioms OrdivonR21.impact_monotone_in_declared_edges
#print axioms OrdivonR21.recheck_dominates_unknown
#print axioms OrdivonR21.unrelated_lego_not_impacted

-- Machine-checked bridge between the existing two native mathematical models:
-- Boolean graph reachability (#978) and the three-priority impact demand
-- (#977). The reversed edge is intentional: PriorityClosure edges point
-- consumer->prerequisite, ImpactReach edges prerequisite->consumer.
namespace OrdivonR21.PriorityClosure

private theorem reach_change_roots {Node : Type}
    (edges : Node → Node → Prop) (fromRoot toRoot : Node → Prop)
    (hRoot : ∀ n, fromRoot n → toRoot n)
    {node} (hReach : OrdivonR21.ImpactReach edges fromRoot node) :
    OrdivonR21.ImpactReach edges toRoot node := by
  induction hReach with
  | origin n h => exact OrdivonR21.ImpactReach.origin n (hRoot n h)
  | successor a b _ hEdge ih =>
      exact OrdivonR21.ImpactReach.successor a b ih hEdge

theorem demand_iff_typed_impact_reach {Node : Type}
    (base : Node → Nat) (consumerRequires : Node → Node → Prop)
    (node : Node) (threshold : Nat) :
    Demand base consumerRequires node threshold ↔
      OrdivonR21.ImpactReach
        (fun prerequisite consumer => consumerRequires consumer prerequisite)
        (fun n => threshold ≤ base n) node := by
  constructor
  · intro hDemand
    induction hDemand with
    | seed h => exact OrdivonR21.ImpactReach.origin _ h
    | consumer hEdge _ ih =>
        exact OrdivonR21.ImpactReach.successor _ _ ih hEdge
  · intro hReach
    induction hReach with
    | origin _ h => exact Demand.seed h
    | successor _ _ _ hEdge ih => exact Demand.consumer hEdge ih

theorem demand_reach_respects_root_predicate {Node : Type}
    (base : Node → Nat) (consumerRequires : Node → Node → Prop)
    (root : Node → Prop) (threshold : Nat)
    (hRoot : ∀ n, threshold ≤ base n ↔ root n)
    (node : Node) :
    Demand base consumerRequires node threshold ↔
      OrdivonR21.ImpactReach
        (fun prerequisite consumer => consumerRequires consumer prerequisite)
        root node := by
  constructor
  · intro h
    apply reach_change_roots _ (fun n => threshold ≤ base n) root
      (fun n hn => (hRoot n).mp hn)
    exact (demand_iff_typed_impact_reach base consumerRequires node threshold).mp h
  · intro h
    apply (demand_iff_typed_impact_reach base consumerRequires node threshold).mpr
    exact reach_change_roots _ root (fun n => threshold ≤ base n)
      (fun n hn => (hRoot n).mpr hn) h

theorem recheck_is_impact_reach {Node : Type}
    (base : Node → Nat) (consumerRequires : Node → Node → Prop)
    (changed : Node → Prop)
    (hChanged : ∀ node, 2 ≤ base node ↔ changed node)
    (node : Node) :
    RecheckDemand base consumerRequires node ↔
      OrdivonR21.StandsAt
        (fun prerequisite consumer => consumerRequires consumer prerequisite)
        changed (fun _ => False) node .recheck := by
  exact demand_reach_respects_root_predicate base consumerRequires changed 2 hChanged node


private theorem impact_reach_union {Node : Type}
    (edge : Node → Node → Prop) (left right : Node → Prop) (node : Node) :
    OrdivonR21.ImpactReach edge (fun n => left n ∨ right n) node ↔
      (OrdivonR21.ImpactReach edge left node ∨
        OrdivonR21.ImpactReach edge right node) := by
  constructor
  · intro h
    induction h with
    | origin n h =>
        cases h with
        | inl hl => exact Or.inl (OrdivonR21.ImpactReach.origin n hl)
        | inr hr => exact Or.inr (OrdivonR21.ImpactReach.origin n hr)
    | successor a b _ hedge ih =>
        cases ih with
        | inl hl => exact Or.inl (OrdivonR21.ImpactReach.successor a b hl hedge)
        | inr hr => exact Or.inr (OrdivonR21.ImpactReach.successor a b hr hedge)
  · intro h
    cases h with
    | inl hl =>
        exact reach_change_roots edge left (fun n => left n ∨ right n)
          (fun _ h => Or.inl h) hl
    | inr hr =>
        exact reach_change_roots edge right (fun n => left n ∨ right n)
          (fun _ h => Or.inr h) hr

-- The actual two-source changed/unknown graph status (#978) and the
-- three-priority status (#977) are definitionally equivalent when and ONLY
-- when the local rank thresholds faithfully encode the actual source sets.
-- The two threshold calibration premises are not inferred from agent identity
-- or unverified dynamic readset completeness.
theorem unknown_only_iff_typed_impact_standing {Node : Type}
    (base : Node → Nat) (consumerRequires : Node → Node → Prop)
    (changed unresolved : Node → Prop)
    (hTwo : ∀ n, 2 ≤ base n ↔ changed n)
    (hOne : ∀ n, 1 ≤ base n ↔ changed n ∨ unresolved n)
    (node : Node) :
    UnknownOnlyDemand base consumerRequires node ↔
      OrdivonR21.StandsAt
        (fun prerequisite consumer => consumerRequires consumer prerequisite)
        changed unresolved node .unknown := by
  let reversed := fun prerequisite consumer => consumerRequires consumer prerequisite
  have hRecheck := demand_reach_respects_root_predicate base consumerRequires changed 2 hTwo node
  have hMaybe := demand_reach_respects_root_predicate base consumerRequires
    (fun n => changed n ∨ unresolved n) 1 hOne node
  have hUnion := impact_reach_union reversed changed unresolved node
  change (Demand base consumerRequires node 1 ∧ ¬ Demand base consumerRequires node 2) ↔
    (¬ OrdivonR21.ImpactReach reversed changed node ∧
      OrdivonR21.ImpactReach reversed unresolved node)
  constructor
  · intro h
    have noChange : ¬ OrdivonR21.ImpactReach reversed changed node := by
      intro hc
      exact h.2 (hRecheck.mpr hc)
    have hOr := hUnion.mp (hMaybe.mp h.1)
    cases hOr with
    | inl hc => exact False.elim (noChange hc)
    | inr hu => exact ⟨noChange, hu⟩
  · intro h
    constructor
    · apply hMaybe.mpr
      apply hUnion.mpr
      exact Or.inr h.2
    · intro hard
      exact h.1 (hRecheck.mp hard)

theorem reuse_candidate_iff_typed_impact_standing {Node : Type}
    (base : Node → Nat) (consumerRequires : Node → Node → Prop)
    (changed unresolved : Node → Prop)
    (hTwo : ∀ n, 2 ≤ base n ↔ changed n)
    (hOne : ∀ n, 1 ≤ base n ↔ changed n ∨ unresolved n)
    (node : Node) :
    ReuseCandidateDemand base consumerRequires node ↔
      OrdivonR21.StandsAt
        (fun prerequisite consumer => consumerRequires consumer prerequisite)
        changed unresolved node .reuseCandidate := by
  let reversed := fun prerequisite consumer => consumerRequires consumer prerequisite
  have hRecheck := demand_reach_respects_root_predicate base consumerRequires changed 2 hTwo node
  have hMaybe := demand_reach_respects_root_predicate base consumerRequires
    (fun n => changed n ∨ unresolved n) 1 hOne node
  have hUnion := impact_reach_union reversed changed unresolved node
  change (¬ Demand base consumerRequires node 1 ∧ ¬ Demand base consumerRequires node 2) ↔
    (¬ OrdivonR21.ImpactReach reversed changed node ∧
      ¬ OrdivonR21.ImpactReach reversed unresolved node)
  constructor
  · intro h
    have noUnion : ¬ OrdivonR21.ImpactReach reversed
        (fun n => changed n ∨ unresolved n) node := by
      intro hu
      exact h.1 (hMaybe.mpr hu)
    constructor
    · intro hc
      exact noUnion (hUnion.mpr (Or.inl hc))
    · intro hu
      exact noUnion (hUnion.mpr (Or.inr hu))
  · intro h
    constructor
    · intro hd
      have hdOr := hUnion.mp (hMaybe.mp hd)
      cases hdOr with
      | inl hc => exact h.1 hc
      | inr hu => exact h.2 hu
    · intro hd
      exact h.1 (hRecheck.mp hd)


-- Non-vacuity counterexample: if a changed root is NOT assigned priority 2,
-- mathematical reachability can demand recheck while rank propagation misses it.
-- Thus the pointwise calibration obligation hTwo is indispensable.
theorem missing_changed_seed_calibration_breaks_recheck_bridge :
    ∃ (base : Bool → Nat) (requires : Bool → Bool → Prop)
      (changed : Bool → Prop) (node : Bool),
      OrdivonR21.ImpactReach
        (fun upstream downstream => requires downstream upstream)
        changed node ∧ ¬ RecheckDemand base requires node := by
  refine ⟨(fun _ => 0), (fun _ _ => False), (fun n => n = true), true, ?_, ?_⟩
  · exact OrdivonR21.ImpactReach.origin true rfl
  · intro hDemand
    have hImpossible : 2 ≤ (0 : Nat) := by
      cases hDemand with
      | seed h => exact h
      | consumer hEdge _ => exact False.elim hEdge
    exact (by decide : ¬ (2 ≤ (0 : Nat))) hImpossible

end OrdivonR21.PriorityClosure

#print axioms OrdivonR21.PriorityClosure.demand_iff_typed_impact_reach
#print axioms OrdivonR21.PriorityClosure.demand_reach_respects_root_predicate
#print axioms OrdivonR21.PriorityClosure.recheck_is_impact_reach
#print axioms OrdivonR21.PriorityClosure.unknown_only_iff_typed_impact_standing
#print axioms OrdivonR21.PriorityClosure.reuse_candidate_iff_typed_impact_standing
#print axioms OrdivonR21.PriorityClosure.missing_changed_seed_calibration_breaks_recheck_bridge

-- Audit the new canonical R2.1 saturated-contract bridge for extra axioms.
#print axioms OrdivonR21.safety_satisfaction_iff_saturated
#print axioms OrdivonR21.refinement_iff_saturated_guarantee
#print axioms OrdivonR21.narrowed_assumptions_cannot_substitute

-- K1 bounded Harness -> Gateway -> Runtime timeout connection, as a
-- mathematical input adapter ONLY. Gateway/Python/Rust implementation
-- refinement and installed Runtime defaults are separate proof obligations.
-- The absent optional Agent timeout must not erase the caller's grant.
namespace OrdivonR21.TimeoutConnection

def forwarded (grant : Nat) (requested : Option Nat) : Nat :=
  requested.getD grant

def admitted (grant : Nat) : Option Nat → Prop
  | none => 0 < grant
  | some timeout => 0 < timeout ∧ timeout ≤ grant

theorem accepted_request_preserves_grant
    (grant : Nat) (requested : Option Nat)
    (h : admitted grant requested) :
    0 < forwarded grant requested ∧ forwarded grant requested ≤ grant := by
  cases requested with
  | none =>
      exact ⟨h, Nat.le_refl grant⟩
  | some timeout =>
      exact h

theorem absent_request_uses_caller_grant (grant : Nat) :
    forwarded grant none = grant := rfl

theorem explicit_request_preserves_admitted_value
    (grant timeout : Nat)
    (_h : admitted grant (some timeout)) :
    forwarded grant (some timeout) = timeout := rfl

-- Nonvacuous model counterexample: delegating absent timeout to a
-- wider downstream default loses the upstream authorized bound.
theorem runtime_default_can_exceed_caller_grant :
    ∃ (grant runtimeDefault : Nat),
      0 < grant ∧ grant < runtimeDefault ∧
      forwarded grant none ≤ grant ∧ ¬ runtimeDefault ≤ grant := by
  exact ⟨10000, 86400000, by decide, by decide, by decide, by decide⟩

-- Strict, task-local R2.1 LEGO profile demanded for this admitted K1
-- responsibility. I/O/S are ACTUAL Lean types, not untyped JSON labels.
-- Extra identity, responsibility, and acceptance retain the six practical
-- roles; each of the eleven historical coordinates is mandatory HERE.
-- This structure is a formal model, not a new registry/runtime or proof
-- that an arbitrary Python/Rust binary implements it.
structure StrictLego21 (I O S : Type) where
  identity : String
  responsibility : String
  pre : S → I → Prop
  post : S → I → O → S → Prop
  inv : S → Prop
  eff : S → I → O → S → Prop
  c : S → I → Nat
  epsilon : Nat
  prov : String
  unfold : List String
  accept : S → I → O → S → Prop

-- Coordinates, in order:
-- I = Option Nat (the optional Agent timeout),
-- O = Nat (explicit forwarded timeout), S = Nat (the caller grant).
-- pre = admitted, post = exact forwarding and preserved grant,
-- inv = positive and bounded grant, eff = this adapter has no state change,
-- c = one ABSTRACT projection step, epsilon = zero numeric approximation,
-- prov = source-level traceability (NOT installed currentness),
-- unfold = one existing Harness adapter responsibility.
def strictTimeout : StrictLego21 (Option Nat) Nat Nat where
  identity := "harness.gateway.execution.timeout-bound-r21"
  responsibility := "preserve caller timeout grant across optional Agent port"
  pre := fun grant requested => admitted grant requested
  post := fun grant requested outgoing next =>
    outgoing = forwarded grant requested ∧ next = grant
  inv := fun grant => 0 < grant ∧ grant ≤ 900000
  eff := fun grant _ _ next => next = grant
  c := fun _ _ => 1
  epsilon := 0
  prov := "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
  unfold := ["PluginGatewayExecutionGrant", "GatewayMcpRuntimeAdapter"]
  accept := fun grant requested outgoing next =>
    outgoing = forwarded grant requested ∧
    next = grant ∧
    0 < outgoing ∧ outgoing ≤ grant

def asIOContract {I O S : Type} (lego : StrictLego21 I O S) :
    IOContract (S × I) (O × S) where
  assume := fun x => lego.inv x.1 ∧ lego.pre x.1 x.2
  guarantee := fun x y =>
    lego.post x.1 x.2 y.1 y.2 ∧
    lego.eff x.1 x.2 y.1 y.2 ∧
    lego.accept x.1 x.2 y.1 y.2

-- The OLD contract is owned by existing Harness consumers, independent of
-- the replacement candidate's invariant/precondition definitions. Without
-- independence, narrowing the new admissible grant range also silently
-- narrows this old domain, making a claimed refinement tautological.
-- The 1..900000 millisecond limit is the existing source-level grant contract
-- (PluginGatewayExecutionGrant.__post_init__), not a new policy.
def oldConsumerContract : IOContract (Nat × Option Nat) (Nat × Nat) where
  assume := fun x =>
    (0 < x.1 ∧ x.1 ≤ 900000) ∧
      match x.2 with
      | none => True
      | some requested => 0 < requested ∧ requested ≤ x.1
  guarantee := fun x y => 0 < y.1 ∧ y.1 ≤ x.1 ∧ y.2 = x.1

-- The mathematical implementation transition is explicitly deterministic.
-- Its equality with the native Python branch still requires an independent
-- trusted program/source-to-model bridge; this statement cannot mint one.
def modeledBehavior :
    (Nat × Option Nat) → (Nat × Nat) → Prop :=
  fun x y => y = (forwarded x.1 x.2, x.1)

theorem strictTimeout_refines_existing_consumer :
    Refines (asIOContract strictTimeout) oldConsumerContract := by
  constructor
  · intro ⟨grant, requested⟩ hOld
    dsimp [oldConsumerContract] at hOld
    rcases hOld with ⟨hGrant, hRequest⟩
    refine ⟨hGrant, ?_⟩
    cases requested with
    | none => exact hGrant.1
    | some t => exact hRequest
  · intro x y hOld hNew
    rcases hNew with ⟨_hPost, hEff, hAccept⟩
    rcases hAccept with ⟨_hExact, _hState, hPositive, hBounded⟩
    exact ⟨hPositive, hBounded, hEff⟩

-- A genuine old consumer admits every established owner-grant value.
-- Shrinking the candidate's invariant must NOT shrink that old admission.
-- This is a permanent independent negative refinement witness.
def narrowedTimeout : StrictLego21 (Option Nat) Nat Nat :=
  { strictTimeout with inv := fun grant => grant = 10000 }

theorem narrowed_candidate_is_nonvacuous :
    ∃ (grant : Nat) (requested : Option Nat),
      narrowedTimeout.inv grant ∧ narrowedTimeout.pre grant requested := by
  exact ⟨10000, none, rfl, (by change 0 < 10000; decide)⟩

theorem narrowed_candidate_cannot_replace_old_consumer :
    ¬ Refines (asIOContract narrowedTimeout) oldConsumerContract := by
  intro hRef
  have hOld : oldConsumerContract.assume (300000, none) := by
    change (0 < 300000 ∧ 300000 ≤ 900000) ∧ True
    exact ⟨⟨by decide, by decide⟩, trivial⟩
  have hNew := hRef.1 (300000, none) hOld
  have wrong : (300000 : Nat) = 10000 := hNew.1
  exact (by decide : (300000 : Nat) ≠ 10000) wrong

-- The old contract must ALSO retain explicitly requested timeouts.
-- Candidate precondition drift must never change old consumer eligibility.
theorem old_consumer_admits_explicit_50000 :
    oldConsumerContract.assume (300000, some 50000) := by
  change (0 < 300000 ∧ 300000 ≤ 900000) ∧
    (0 < 50000 ∧ 50000 ≤ 300000)
  decide

-- The new candidate remains realizable but rejects a previously admissible
-- explicit timeout, so substitution must fail even when the grant invariant
-- itself is unchanged.
def narrowedRequestTimeout : StrictLego21 (Option Nat) Nat Nat :=
  { strictTimeout with
    pre := fun grant requested =>
      admitted grant requested ∧
        match requested with
        | none => True
        | some timeout => timeout ≤ 10000 }

theorem narrowedRequestTimeout_has_admitted_input :
    ∃ (grant : Nat) (requested : Option Nat),
      narrowedRequestTimeout.inv grant ∧
        narrowedRequestTimeout.pre grant requested := by
  refine ⟨10000, some 5000, ?_, ?_⟩
  · change 0 < 10000 ∧ 10000 ≤ 900000
    decide
  · change (0 < 5000 ∧ 5000 ≤ 10000) ∧ 5000 ≤ 10000
    decide

theorem narrowedRequestTimeout_cannot_replace_oldConsumer :
    ¬ Refines (asIOContract narrowedRequestTimeout) oldConsumerContract := by
  intro hRef
  have hNew := hRef.1 (300000, some 50000)
    old_consumer_admits_explicit_50000
  have hBound : (50000 : Nat) ≤ 10000 := hNew.2.2
  exact (by decide : ¬ ((50000 : Nat) ≤ 10000)) hBound

theorem modeledBehavior_implements_strictTimeout :
    Implements (asIOContract strictTimeout) modeledBehavior := by
  constructor
  · intro x y hAssume hBehavior
    subst y
    dsimp [asIOContract, strictTimeout, modeledBehavior] at *
    refine ⟨⟨rfl, rfl⟩, rfl, ⟨rfl, rfl, ?_⟩⟩
    exact accepted_request_preserves_grant x.1 x.2 hAssume.2
  · intro x _
    exact ⟨(forwarded x.1 x.2, x.1), rfl⟩

theorem modeledBehavior_preserves_old_consumer :
    Implements oldConsumerContract modeledBehavior :=
  refinement_preserves_implementation
    (asIOContract strictTimeout) oldConsumerContract modeledBehavior
    modeledBehavior_implements_strictTimeout
    strictTimeout_refines_existing_consumer

-- This obligation is stronger than mere invariant satisfiability:
-- every accepted modeled step preserves its state invariant.
theorem strictTimeout_preserves_invariant
    (grant : Nat) (requested : Option Nat)
    (outgoing next : Nat)
    (hInv : strictTimeout.inv grant)
    (hPost : strictTimeout.post grant requested outgoing next) :
    strictTimeout.inv next := by
  rw [hPost.2]
  exact hInv

-- The cost/approximation coordinates are intentionally abstract: a single
-- projection step, with no mathematical approximation of the timeout value.
-- They are not latency, monetary cost, installed effects or proof reliability.
theorem strictTimeout_abstract_cost_and_epsilon
    (grant : Nat) (requested : Option Nat) :
    strictTimeout.c grant requested = 1 ∧ strictTimeout.epsilon = 0 :=
  ⟨rfl, rfl⟩

-- The admitted mathematical realization exactly matches the declared
-- effect/acceptance relation, not just the old bounded consumer guarantee.
theorem strictTimeout_transition_meets_acceptance
    (grant : Nat) (requested : Option Nat)
    (hInv : strictTimeout.inv grant)
    (hPre : strictTimeout.pre grant requested) :
    strictTimeout.post grant requested
      (forwarded grant requested) grant ∧
    strictTimeout.eff grant requested
      (forwarded grant requested) grant ∧
    strictTimeout.accept grant requested
      (forwarded grant requested) grant := by
  have hBound := accepted_request_preserves_grant grant requested hPre
  exact ⟨⟨rfl, rfl⟩, rfl, ⟨rfl, rfl, hBound⟩⟩

-- Exact, non-vacuous admitted source input, so success cannot be obtained
-- merely because the input assumptions are contradictory.
theorem strictTimeout_has_admitted_input :
    ∃ (grant : Nat) (requested : Option Nat),
      strictTimeout.inv grant ∧ strictTimeout.pre grant requested := by
  refine ⟨10000, none, ?_, ?_⟩
  · change 0 < 10000 ∧ 10000 ≤ 900000
    exact ⟨by decide, by decide⟩
  · change admitted 10000 none
    exact (by decide : 0 < 10000)

-- An uncontrolled downstream default violates the old consumer guarantee.
-- The countermodel is concrete and cannot be disguised as a compatible
-- refinement merely by supplying an arbitrary evidence reference.
theorem unbounded_default_not_a_refinement :
    ¬ oldConsumerContract.guarantee
      (10000, none) (86400000, 10000) := by
  intro h
  have hBad : 86400000 ≤ 10000 := h.2.1
  exact (by decide : ¬ (86400000 ≤ 10000)) hBad

end OrdivonR21.TimeoutConnection

#print axioms OrdivonR21.TimeoutConnection.old_consumer_admits_explicit_50000
#print axioms OrdivonR21.TimeoutConnection.narrowedRequestTimeout_has_admitted_input
#print axioms OrdivonR21.TimeoutConnection.narrowedRequestTimeout_cannot_replace_oldConsumer
#print axioms OrdivonR21.TimeoutConnection.narrowed_candidate_is_nonvacuous
#print axioms OrdivonR21.TimeoutConnection.narrowed_candidate_cannot_replace_old_consumer
#print axioms OrdivonR21.TimeoutConnection.modeledBehavior_implements_strictTimeout
#print axioms OrdivonR21.TimeoutConnection.strictTimeout_refines_existing_consumer
#print axioms OrdivonR21.TimeoutConnection.modeledBehavior_preserves_old_consumer
#print axioms OrdivonR21.TimeoutConnection.strictTimeout_has_admitted_input
#print axioms OrdivonR21.TimeoutConnection.unbounded_default_not_a_refinement
#print axioms OrdivonR21.TimeoutConnection.strictTimeout_preserves_invariant
#print axioms OrdivonR21.TimeoutConnection.strictTimeout_abstract_cost_and_epsilon
#print axioms OrdivonR21.TimeoutConnection.strictTimeout_transition_meets_acceptance

#print axioms OrdivonR21.TimeoutConnection.accepted_request_preserves_grant
#print axioms OrdivonR21.TimeoutConnection.absent_request_uses_caller_grant
#print axioms OrdivonR21.TimeoutConnection.explicit_request_preserves_admitted_value
#print axioms OrdivonR21.TimeoutConnection.runtime_default_can_exceed_caller_grant

-- R2.1 Representation-first / Equivalence-first: an evidence identity is
-- stable only if source numeric meaning is preserved by the chosen encoding.
-- This is the MODEL contract for the Composition JSON Decimal/Float boundary.
-- The real Python Decimal/float admission check remains a separate
-- implementation refinement obligation; it is not established by this proof.
namespace OrdivonR21.NumericRepresentation

universe u v
theorem qualified_same_encoding_implies_same_exact_value
    {Exact : Type u} {Encoded : Type v}
    (decodeCanonical : Encoded → Exact)
    {a b : Exact} {encodedA encodedB : Encoded}
    (acceptA : a = decodeCanonical encodedA)
    (acceptB : b = decodeCanonical encodedB)
    (sameEncoding : encodedA = encodedB) : a = b := by
  calc
    a = decodeCanonical encodedA := acceptA
    _ = decodeCanonical encodedB := congrArg decodeCanonical sameEncoding
    _ = b := acceptB.symm

-- If two exact source values differ, the same encoded output cannot ACCEPT
-- BOTH lexemes. At least one must be refused instead of reusing its digest.
theorem different_source_same_encoding_requires_refusal
    {Exact : Type u} {Encoded : Type v}
    (decodeCanonical : Encoded → Exact)
    {a b : Exact} {encodedA encodedB : Encoded}
    (differentSource : a ≠ b)
    (sameEncoding : encodedA = encodedB) :
    ¬ (a = decodeCanonical encodedA ∧ b = decodeCanonical encodedB) := by
  intro bothAccepted
  exact differentSource
    (qualified_same_encoding_implies_same_exact_value decodeCanonical
      bothAccepted.1 bothAccepted.2 sameEncoding)

-- Non-vacuity: a many-to-one representation without the admission predicate
-- DOES have distinct source values sharing the same encoded identity.
theorem unchecked_numeric_alias_is_possible :
    ∃ (encode : Bool → Nat) (a b : Bool),
      a ≠ b ∧ encode a = encode b := by
  exact ⟨(fun _ => 0), false, true, by decide, rfl⟩

end OrdivonR21.NumericRepresentation

#print axioms OrdivonR21.NumericRepresentation.qualified_same_encoding_implies_same_exact_value
#print axioms OrdivonR21.NumericRepresentation.different_source_same_encoding_requires_refusal
#print axioms OrdivonR21.NumericRepresentation.unchecked_numeric_alias_is_possible

-- R2.1 K1/Cross-Agent evidence message LEGO, one scoped responsibility.
-- ell_M = (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold):
-- I=(ref,digest) of an already authenticated, open-topic message;
-- O=(success status, unchanged or appended ledger); S=ref→(digest,seq), nextSeq;
-- pre=ref and digest nonempty; authorized writer/open topic/transactional
--      admission are externally required preconditions, not proven by Lean;
-- post=matching replay returns existing, conflicting digest refuses mutation,
--      unseen ref appends exactly once, no other ref is changed;
-- inv=previously committed digest and order never silently change;
-- eff=one append or none (not downstream execution);
-- c=one abstract atomic insertion; epsilon=0 in this exact finite-step model;
-- prov=Host v2 social_store.post_message ON CONFLICT/transaction sourcecut;
-- unfold=(Gateway.message_post, Host.post_message, Host.topic_resume).
-- These are mandatory *for this instantiated LEGO*; this namespace is NOT a
-- universal metadata registry. SQL isolation, network authentication, the
-- actual Python implementation, installed revision, and result-currentness
-- are independent K2 refinement obligations, NOT claimed here.
namespace OrdivonR21.MessageEvidence

-- This ledger is a LOGICAL successful-commit projection: nextSeq is
-- an abstract ordinal, NOT PostgreSQL nextval(), which may have gaps.
-- The physical wire sequence, request-receipt table and allocator are
-- outside this modeled observation universe. K2 must separately prove an
-- order-preserving realization to wire sequences. Equality is NOT assumed.
structure Ledger where
  messages : String → Option (String × Nat)
  nextSeq : Nat

inductive Admission where
  | committed
  | existing
  | conflict
  deriving DecidableEq

def append (s : Ledger) (ref digest : String) : Ledger :=
  { messages := fun k =>
      if k = ref then some (digest, s.nextSeq) else s.messages k
    nextSeq := s.nextSeq + 1 }

def deliver (s : Ledger) (ref digest : String) : Ledger × Admission :=
  match s.messages ref with
  | none => (append s ref digest, .committed)
  | some (oldDigest, _) =>
      if oldDigest = digest then (s, .existing) else (s, .conflict)

-- Positive and negative results follow by full case analysis, with no
-- axioms for delivery or external verifier success.
theorem same_ref_digest_replay_is_state_preserving
    (s : Ledger) (ref digest : String) (seq : Nat)
    (h : s.messages ref = some (digest, seq)) :
    deliver s ref digest = (s, .existing) := by
  simp [deliver, h]

theorem different_digest_conflict_is_state_preserving
    (s : Ledger) (ref stored incoming : String) (seq : Nat)
    (h : s.messages ref = some (stored, seq))
    (hDifferent : stored ≠ incoming) :
    deliver s ref incoming = (s, .conflict) := by
  simp [deliver, h, hDifferent]

theorem fresh_ref_appends_once
    (s : Ledger) (ref digest : String)
    (h : s.messages ref = none) :
    (deliver s ref digest).2 = .committed ∧
    (deliver s ref digest).1.messages ref =
      some (digest, s.nextSeq) ∧
    (deliver s ref digest).1.nextSeq = s.nextSeq + 1 := by
  simp [deliver, h, append]

theorem fresh_ref_does_not_mutate_other_messages
    (s : Ledger) (ref digest other : String)
    (h : s.messages ref = none) (hOther : other ≠ ref) :
    (deliver s ref digest).1.messages other = s.messages other := by
  simp [deliver, h, append, hOther]

-- State-transition semantics: the first delivery commits, any identical
-- repeated delivery returns the SAME state. No second sequence allocation.
theorem fresh_then_replay_is_idempotent
    (s : Ledger) (ref digest : String)
    (h : s.messages ref = none) :
    deliver (deliver s ref digest).1 ref digest =
      ((deliver s ref digest).1, .existing) := by
  have hInserted :
      (deliver s ref digest).1.messages ref =
        some (digest, s.nextSeq) := (fresh_ref_appends_once s ref digest h).2.1
  exact same_ref_digest_replay_is_state_preserving
    (deliver s ref digest).1 ref digest s.nextSeq hInserted

-- A non-constant abstract specification is deliberately independent of the
-- algorithm: it constrains every previously present message and all new
-- references, including unrelated references.
def Guarantees (input : Ledger × String × String)
    (output : Ledger × Admission) : Prop :=
  let s := input.1
  let ref := input.2.1
  let digest := input.2.2
  let next := output.1
  let status := output.2
  (∀ old seq, s.messages ref = some (old, seq) →
      next = s ∧ (if old = digest then status = .existing
                  else status = .conflict)) ∧
  (s.messages ref = none →
      status = .committed ∧
      next.messages ref = some (digest, s.nextSeq) ∧
      next.nextSeq = s.nextSeq + 1 ∧
      ∀ other, other ≠ ref → next.messages other = s.messages other)

def protocol : IOContract (Ledger × String × String) (Ledger × Admission) :=
  { assume := fun i => i.2.1 ≠ "" ∧ i.2.2 ≠ ""
    guarantee := Guarantees }

def executableModel (input : Ledger × String × String)
    (output : Ledger × Admission) : Prop :=
  output = deliver input.1 input.2.1 input.2.2

-- Admitted problem instances demonstrably exist; model satisfaction is not
-- achieved by assuming an impossible or empty input domain.
theorem protocol_assumptions_are_nonvacuous :
    ∃ (input : Ledger × String × String), protocol.assume input := by
  refine ⟨({ messages := fun _ => none, nextSeq := 1 }, "ref", "digest"), ?_⟩
  simp [protocol]

-- Strict model-level refinement to the INDEPENDENT behavioral postcondition,
-- with totality for every admitted input. This does NOT certify Host Python
-- or Postgres as an implementation of executableModel.
theorem executable_model_refines_protocol :
    Implements protocol executableModel := by
  constructor
  · intro ⟨s, ref, digest⟩ output _ hExec
    subst output
    change Guarantees (s, ref, digest) (deliver s ref digest)
    unfold Guarantees
    constructor
    · intro old seq hOld
      change s.messages ref = some (old, seq) at hOld
      by_cases hd : old = digest
      · subst old
        simp [deliver, hOld]
      · simp [deliver, hOld, hd]
    · intro hFresh
      change s.messages ref = none at hFresh
      constructor
      · simp [deliver, hFresh]
      constructor
      · simp [deliver, hFresh, append]
      constructor
      · simp [deliver, hFresh, append]
      · intro other hOther
        change other ≠ ref at hOther
        simp [deliver, hFresh, append, hOther]
  · intro ⟨s, ref, digest⟩ _
    exact ⟨deliver s ref digest, rfl⟩

-- Counterexample when the assumed uniqueness/atomicity contract is removed:
-- overwriting a previously committed digest cannot satisfy this protocol.
theorem overwrite_breaks_existing_immutability :
    ∃ (s : Ledger) (ref old incoming : String) (seq : Nat),
      old ≠ incoming ∧
      s.messages ref = some (old, seq) ∧
      ¬ Guarantees (s, ref, incoming)
        (append s ref incoming, .committed) := by
  let s : Ledger := { messages := fun _ => some ("old", 0), nextSeq := 1 }
  refine ⟨s, "message", "old", "new", 0, by decide, rfl, ?_⟩
  intro h
  have hConflict := (h.1 "old" 0 rfl).2
  simp at hConflict

-- Instantiate the EXISTING R2.1 typed 11-coordinate component carrier
-- from TimeoutConnection. This models one real collaboration responsibility;
-- it does not create another transport, registry, framework or evaluator.
def LedgerInvariant (s : Ledger) : Prop :=
  0 < s.nextSeq ∧
    ∀ ref digest seq, s.messages ref = some (digest, seq) →
      seq < s.nextSeq

theorem append_preserves_ledger_invariant (s : Ledger) (ref digest : String)
    (hInv : LedgerInvariant s) :
    LedgerInvariant (append s ref digest) := by
  constructor
  · exact Nat.zero_lt_succ s.nextSeq
  · intro key stored seq hStored
    change (if key = ref then some (digest, s.nextSeq) else s.messages key) =
      some (stored, seq) at hStored
    change seq < s.nextSeq + 1
    by_cases hKey : key = ref
    · rw [if_pos hKey] at hStored
      cases hStored
      exact Nat.lt_succ_self s.nextSeq
    · rw [if_neg hKey] at hStored
      exact Nat.lt_trans (hInv.2 key stored seq hStored)
        (Nat.lt_succ_self s.nextSeq)

theorem deliver_preserves_ledger_invariant (s : Ledger) (ref digest : String)
    (hInv : LedgerInvariant s) :
    LedgerInvariant (deliver s ref digest).1 := by
  unfold deliver
  cases h : s.messages ref with
  | none =>
      simpa [h] using append_preserves_ledger_invariant s ref digest hInv
  | some old =>
      by_cases same : old.1 = digest
      · simpa [h, same] using hInv
      · simpa [h, same] using hInv

def strictMessage :
    OrdivonR21.TimeoutConnection.StrictLego21
      (String × String) Admission Ledger where
  identity := "host.space.message.post-and-replay-r21"
  responsibility := "atomic durable message admission with immutable identity"
  pre := fun _ request => request.1 ≠ "" ∧ request.2 ≠ ""
  post := fun s request admission next =>
    deliver s request.1 request.2 = (next, admission)
  inv := LedgerInvariant
  eff := fun s _ admission next =>
    (admission = .committed → next.nextSeq = s.nextSeq + 1) ∧
    (admission ≠ .committed → next = s)
  c := fun _ _ => 1
  epsilon := 0
  prov := "services/host/src/ordivon_host_v2/social_store.py:post_message"
  unfold := ["Gateway.message_post", "Host.social_store.post_message",
             "Host.topic_resume"]
  accept := fun s request admission next =>
    Guarantees (s, request.1, request.2) (next, admission)

def oldMessageConsumer : IOContract
    (Ledger × String × String) (Admission × Ledger) where
  assume := fun x => LedgerInvariant x.1 ∧
    x.2.1 ≠ "" ∧ x.2.2 ≠ ""
  guarantee := fun x y =>
    Guarantees (x.1, x.2.1, x.2.2) (y.2, y.1)

def strictMessageBehavior (x : Ledger × String × String)
    (y : Admission × Ledger) : Prop :=
  deliver x.1 x.2.1 x.2.2 = (y.2, y.1)

-- Exact effect discipline follows from the three independent cases of the
-- durable-message model (fresh, same digest, conflicting digest).
theorem admitted_delivery_effect (s : Ledger) (ref digest : String) :
    let result := deliver s ref digest
    (result.2 = .committed → result.1.nextSeq = s.nextSeq + 1) ∧
    (result.2 ≠ .committed → result.1 = s) := by
  cases h : s.messages ref with
  | none =>
      simp [deliver, h, append]
  | some entry =>
      by_cases same : entry.1 = digest
      · simp [deliver, h, same]
      · simp [deliver, h, same]

theorem strict_message_model_implements_contract :
    Implements
      (OrdivonR21.TimeoutConnection.asIOContract strictMessage)
      strictMessageBehavior := by
  constructor
  · intro ⟨s, ref, digest⟩ ⟨admission, next⟩ hAssume hBehavior
    change deliver s ref digest = (next, admission) at hBehavior
    change LedgerInvariant s ∧
      (ref ≠ "" ∧ digest ≠ "") at hAssume
    change
      (deliver s ref digest = (next, admission)) ∧
      ((admission = .committed → next.nextSeq = s.nextSeq + 1) ∧
       (admission ≠ .committed → next = s)) ∧
      Guarantees (s, ref, digest) (next, admission)
    constructor
    · exact hBehavior
    constructor
    · have hEffect := admitted_delivery_effect s ref digest
      rw [hBehavior] at hEffect
      exact hEffect
    · have hOld : protocol.assume (s, ref, digest) := hAssume.2
      have hModel : executableModel (s, ref, digest) (next, admission) :=
        hBehavior.symm
      exact executable_model_refines_protocol.1
        (s, ref, digest) (next, admission) hOld hModel
  · intro ⟨s, ref, digest⟩ _
    exact ⟨((deliver s ref digest).2, (deliver s ref digest).1), rfl⟩

theorem strict_message_refines_existing_consumer :
    Refines
      (OrdivonR21.TimeoutConnection.asIOContract strictMessage)
      oldMessageConsumer := by
  constructor
  · intro x hOld
    exact hOld
  · intro x y _ hNew
    exact hNew.2.2

theorem strict_message_preserves_existing_consumers :
    Implements oldMessageConsumer strictMessageBehavior :=
  refinement_preserves_implementation
    (OrdivonR21.TimeoutConnection.asIOContract strictMessage)
    oldMessageConsumer strictMessageBehavior
    strict_message_model_implements_contract
    strict_message_refines_existing_consumer

theorem strict_message_model_preserves_invariant
    (s : Ledger) (ref digest : String)
    (hInv : strictMessage.inv s) :
    strictMessage.inv (deliver s ref digest).1 :=
  deliver_preserves_ledger_invariant s ref digest hInv

-- Nonvacuity of the full typed invariant and admission precondition.
theorem strict_message_has_admitted_state_and_request :
    ∃ (s : Ledger) (ref digest : String),
      strictMessage.inv s ∧ strictMessage.pre s (ref, digest) := by
  refine ⟨{ messages := fun _ => none, nextSeq := 1 }, "ref", "digest", ?_, ?_⟩
  · constructor
    · exact (by decide : 0 < (1 : Nat))
    · intro ref digest seq h
      cases h
  · exact ⟨by decide, by decide⟩

theorem strict_message_abstract_cost_and_zero_error
    (s : Ledger) (request : String × String) :
    strictMessage.c s request = 1 ∧ strictMessage.epsilon = 0 :=
  ⟨rfl, rfl⟩

end OrdivonR21.MessageEvidence

#print axioms OrdivonR21.MessageEvidence.admitted_delivery_effect
#print axioms OrdivonR21.MessageEvidence.strict_message_model_implements_contract
#print axioms OrdivonR21.MessageEvidence.strict_message_refines_existing_consumer
#print axioms OrdivonR21.MessageEvidence.strict_message_preserves_existing_consumers
#print axioms OrdivonR21.MessageEvidence.strict_message_model_preserves_invariant
#print axioms OrdivonR21.MessageEvidence.strict_message_abstract_cost_and_zero_error
#print axioms OrdivonR21.MessageEvidence.strict_message_has_admitted_state_and_request

#print axioms OrdivonR21.MessageEvidence.same_ref_digest_replay_is_state_preserving
#print axioms OrdivonR21.MessageEvidence.different_digest_conflict_is_state_preserving
#print axioms OrdivonR21.MessageEvidence.fresh_ref_appends_once
#print axioms OrdivonR21.MessageEvidence.fresh_ref_does_not_mutate_other_messages
#print axioms OrdivonR21.MessageEvidence.fresh_then_replay_is_idempotent
#print axioms OrdivonR21.MessageEvidence.protocol_assumptions_are_nonvacuous
#print axioms OrdivonR21.MessageEvidence.executable_model_refines_protocol
#print axioms OrdivonR21.MessageEvidence.overwrite_breaks_existing_immutability



-- Historical v1 projection identity and formal proof standing are different
-- authorities. A caller's SATISFIED string cannot decide theorem validity.
-- This model establishes impossibility of report-only proof, not Python
-- implementation refinement or an installed verifier.
namespace OrdivonR21.ReportIsNotProof

structure ReportedGateWorld where
  callerSaysSatisfied : Bool
  actualSpecificationHolds : Bool

theorem same_satisfied_report_can_hide_opposite_truth :
    ∃ (good bad : ReportedGateWorld),
      good.callerSaysSatisfied = true ∧
      bad.callerSaysSatisfied = true ∧
      good.callerSaysSatisfied = bad.callerSaysSatisfied ∧
      good.actualSpecificationHolds = true ∧
      bad.actualSpecificationHolds = false := by
  refine ⟨⟨true, true⟩, ⟨true, false⟩, ?_, ?_, ?_, ?_, ?_⟩ <;> rfl

theorem no_report_only_decider_can_prove_actual_truth
    (judge : Bool → Bool) :
    ¬ (∀ world : ReportedGateWorld,
         judge world.callerSaysSatisfied = world.actualSpecificationHolds) := by
  intro h
  have hTrue := h ⟨true, true⟩
  have hFalse := h ⟨true, false⟩
  simp only at hTrue hFalse
  rw [hTrue] at hFalse
  exact Bool.noConfusion hFalse

end OrdivonR21.ReportIsNotProof

#print axioms OrdivonR21.ReportIsNotProof.same_satisfied_report_can_hide_opposite_truth
#print axioms OrdivonR21.ReportIsNotProof.no_report_only_decider_can_prove_actual_truth
