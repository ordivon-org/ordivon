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

-- Incremental reasoning edges a CLOSED actual dependency scope, not an
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

def DependencyExtensionality {δ β γ : Type}
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
    (hObserves : DependencyExtensionality actual observable) :
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
      DependencyExtensionality actual observable ∧
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
