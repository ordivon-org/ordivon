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

end OrdivonR21

#print axioms OrdivonR21.closed_dependency_frame
#print axioms OrdivonR21.unlisted_dependency_breaks_frame

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

-- If two exact source values differ, the same encoded output cannot admit
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
