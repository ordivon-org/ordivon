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

def DependsOnlyOn {δ β γ : Type}
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
    (hObserves : DependsOnlyOn actual observable) :
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
      DependsOnlyOn actual observable ∧
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

namespace OrdivonR21

-- R2.1 task-local environment frame theorem.
-- This is an ABSTRACT dependency model, not a proof that an Agent's declared
-- readset is complete, that Python implements it, or that the live environment
-- satisfies the original theorem's assumptions.
namespace ScopedEnvironment

variable {Node Env : Type}

-- A proof consumer can use an environment guarantee directly or use another
-- proof. The edges are typed by their declared logical roles, not file paths.
inductive Reaches (reads : Node → Env → Prop)
    (uses : Node → Node → Prop) : Node → Env → Prop where
  | direct {node env} (edge : reads node env) :
      Reaches reads uses node env
  | relay {node child env}
      (edge : uses node child) (tail : Reaches reads uses child env) :
      Reaches reads uses node env

-- Uncertain environmental evidence taints exactly the declared dependent
-- closure; an unrelated proof need not be re-checked *for this root*.
inductive Impact (reads : Node → Env → Prop)
    (uses : Node → Node → Prop) (unknown : Env → Prop) :
    Node → Prop where
  | direct {node env} (edge : reads node env) (uncertain : unknown env) :
      Impact reads uses unknown node
  | relay {node child} (edge : uses node child)
      (affected : Impact reads uses unknown child) :
      Impact reads uses unknown node

-- Every inferred impact has a real path within this DECLARED graph.
theorem impact_has_declared_path
    (reads : Node → Env → Prop) (uses : Node → Node → Prop)
    (unknown : Env → Prop) {node : Node}
    (affected : Impact reads uses unknown node) :
    ∃ env, Reaches reads uses node env ∧ unknown env := by
  induction affected with
  | direct edge uncertain =>
      exact ⟨_, Reaches.direct edge, uncertain⟩
  | relay edge _ ih =>
      obtain ⟨env, path, uncertain⟩ := ih
      exact ⟨env, Reaches.relay edge path, uncertain⟩

-- Conversely, every root with a declared path is included by propagation.
theorem declared_path_and_unknown_imply_impact
    (reads : Node → Env → Prop) (uses : Node → Node → Prop)
    (unknown : Env → Prop) {node : Node} {env : Env}
    (path : Reaches reads uses node env) (uncertain : unknown env) :
    Impact reads uses unknown node := by
  induction path with
  | direct edge =>
      exact Impact.direct edge uncertain
  | relay edge _ ih =>
      exact Impact.relay edge (ih uncertain)

theorem impact_iff_declared_reachable_unknown
    (reads : Node → Env → Prop) (uses : Node → Node → Prop)
    (unknown : Env → Prop) (node : Node) :
    Impact reads uses unknown node ↔
      ∃ env, Reaches reads uses node env ∧ unknown env := by
  constructor
  · exact impact_has_declared_path reads uses unknown
  · rintro ⟨env, path, uncertain⟩
    exact declared_path_and_unknown_imply_impact reads uses unknown path uncertain

-- Closure cannot be asserted by naming a manifest. It is a theorem PREMISE:
-- every real direct read and real proof-to-proof consumer edge must be included
-- in the declared graph. Under those hypotheses, abstract impact is complete
-- relative to the true graph (not merely a convenient subset of it).
theorem closed_graph_contains_actual_impact
    (actualReads declaredReads : Node → Env → Prop)
    (actualUses declaredUses : Node → Node → Prop)
    (unknown : Env → Prop)
    (closedReads : ∀ node env, actualReads node env → declaredReads node env)
    (closedUses : ∀ node child, actualUses node child → declaredUses node child)
    {node : Node}
    (affected : Impact actualReads actualUses unknown node) :
    Impact declaredReads declaredUses unknown node := by
  induction affected with
  | direct edge uncertain =>
      exact Impact.direct (closedReads _ _ edge) uncertain
  | relay edge _ ih =>
      exact Impact.relay (closedUses _ _ edge) ih

-- Stronger frame: if the declared graph is a sound OVER-approximation of
-- the actual execution footprint, declared non-impact implies actual
-- non-impact. Without this premise the counterexample below refutes it.
theorem closed_graph_frame
    (actualReads declaredReads : Node → Env → Prop)
    (actualUses declaredUses : Node → Node → Prop)
    (unknown : Env → Prop) (node : Node)
    (closedReads : ∀ n e, actualReads n e → declaredReads n e)
    (closedUses : ∀ n m, actualUses n m → declaredUses n m)
    (declaredUnaffected : ¬ Impact declaredReads declaredUses unknown node) :
    ¬ Impact actualReads actualUses unknown node := by
  intro actualAffected
  exact declaredUnaffected
    (closed_graph_contains_actual_impact actualReads declaredReads
      actualUses declaredUses unknown closedReads closedUses actualAffected)

-- Frame: non-reachable root changes cannot taint this node IF the declared
-- graph is complete for the relevant effect/observation footprint.
theorem scoped_frame
    (reads : Node → Env → Prop) (uses : Node → Node → Prop)
    (unknown : Env → Prop) (node : Node)
    (noAffectedPath : ∀ env, Reaches reads uses node env → ¬ unknown env) :
    ¬ Impact reads uses unknown node := by
  intro affected
  obtain ⟨env, path, uncertain⟩ :=
    impact_has_declared_path reads uses unknown affected
  exact noAffectedPath env path uncertain

-- Missing from BOTH environment observations still requires local UNKNOWN,
-- when the graph declares that root and no trustworthy readset-witness exists.
theorem missing_both_observations_implies_local_impact
    (reads : Node → Env → Prop) (uses : Node → Node → Prop)
    (required before after : Env → Prop) {node : Node} {env : Env}
    (edge : reads node env) (need : required env)
    (oldAbsent : ¬ before env) (newAbsent : ¬ after env) :
    Impact reads uses
      (fun e => required e ∧ ¬ before e ∧ ¬ after e) node := by
  exact Impact.direct edge ⟨need, oldAbsent, newAbsent⟩

-- A negative control: if the TRUE execution has an undeclared dependency,
-- its actual affectedness cannot be concluded from the declared graph.
-- This exhibits why a frame theorem without a readset-closure premise is
-- not an installed-effect or consumer-equivalence proof.
theorem missing_dependency_counterexample :
    ∃ (declared actual : Bool → Bool → Prop) (unknown : Bool → Prop),
      ¬ Impact declared (fun _ _ => False) unknown true ∧
      Impact actual (fun _ _ => False) unknown true := by
  let declared : Bool → Bool → Prop := fun _ _ => False
  let actual : Bool → Bool → Prop := fun node env =>
    node = true ∧ env = true
  let unknown : Bool → Prop := fun env => env = true
  refine ⟨declared, actual, unknown, ?_, ?_⟩
  · intro affected
    obtain ⟨env, path, _⟩ :=
      impact_has_declared_path declared (fun _ _ => False) unknown affected
    cases path with
    | direct edge => exact edge
    | relay edge _ => exact edge
  · exact Impact.direct ⟨rfl, rfl⟩ rfl

end ScopedEnvironment

end OrdivonR21

#print axioms OrdivonR21.ScopedEnvironment.closed_graph_frame
#print axioms OrdivonR21.ScopedEnvironment.missing_dependency_counterexample
