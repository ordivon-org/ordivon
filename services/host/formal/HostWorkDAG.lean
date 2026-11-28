-- General (not bounded) graph-theoretic admission theorem for Host Work relations.
-- This is an ABSTRACT theorem: no claims about psycopg, SQL transaction
-- isolation, PostgreSQL advisory locks, deployment or effect authority.

universe u

namespace OrdivonHostDAG

inductive Walk {α : Type u} (E : α → α → Prop) : α → α → Prop where
  | refl (a : α) : Walk E a a
  | step {a b c : α} (hab : E a b) (hbc : Walk E b c) : Walk E a c

def Acyclic {α : Type u} (E : α → α → Prop) : Prop :=
  ∀ a b, E a b → ¬ Walk E b a

def Insert {α : Type u} (E : α → α → Prop) (source target : α) :
    α → α → Prop :=
  fun a b => E a b ∨ (a = source ∧ b = target)

theorem walk_append {α : Type u} {E : α → α → Prop}
    {a b c : α} (hAB : Walk E a b) (hBC : Walk E b c) :
    Walk E a c := by
  induction hAB with
  | refl _ => exact hBC
  | step edge tail ih => exact Walk.step edge (ih hBC)

theorem walk_lift {α : Type u} {E : α → α → Prop}
    {source target a b : α} (h : Walk E a b) :
    Walk (Insert E source target) a b := by
  induction h with
  | refl x => exact Walk.refl x
  | step edge tail ih => exact Walk.step (Or.inl edge) ih

-- Under no existing target -> source path, a walk after insertion
-- either uses zero new edges or exactly one (a -> source -> target -> b).
theorem walk_reduction {α : Type u} {E : α → α → Prop}
    {source target : α} (noBack : ¬ Walk E target source)
    {a b : α} (h : Walk (Insert E source target) a b) :
    Walk E a b ∨ (Walk E a source ∧ Walk E target b) := by
  induction h with
  | refl x => exact Or.inl (Walk.refl x)
  | step edge tail ih =>
    rcases edge with oldEdge | addedEdge
    · rcases ih with oldTail | ⟨toSource, fromTarget⟩
      · exact Or.inl (Walk.step oldEdge oldTail)
      · exact Or.inr ⟨Walk.step oldEdge toSource, fromTarget⟩
    · rcases addedEdge with ⟨rfl, rfl⟩
      rcases ih with oldTail | ⟨toSource, fromTarget⟩
      · exact Or.inr ⟨Walk.refl _, oldTail⟩
      · exact False.elim (noBack toSource)

theorem insert_preserves_acyclic {α : Type u} {E : α → α → Prop}
    {source target : α}
    (before : Acyclic E) (noBack : ¬ Walk E target source) :
    Acyclic (Insert E source target) := by
  intro a b edge path
  have reduced := walk_reduction noBack path
  rcases edge with oldEdge | addedEdge
  · rcases reduced with oldPath | ⟨bToSource, targetToA⟩
    · exact before a b oldEdge oldPath
    · exact noBack (walk_append targetToA (Walk.step oldEdge bToSource))
  · rcases addedEdge with ⟨rfl, rfl⟩
    rcases reduced with oldPath | ⟨targetToSource, _⟩
    · exact noBack oldPath
    · exact noBack targetToSource

theorem insert_creates_cycle_if_backpath {α : Type u}
    {E : α → α → Prop} {source target : α}
    (backPath : Walk E target source) :
    ¬ Acyclic (Insert E source target) := by
  intro after
  have newEdge : Insert E source target source target :=
    Or.inr ⟨rfl, rfl⟩
  exact after source target newEdge (walk_lift backPath)

-- Abstract unbounded theorem. Preconditions are substantive:
-- the before-state is acyclic; write isolation/source refinement
-- are *not* discharged here.
theorem insert_acyclic_iff_no_backpath {α : Type u}
    {E : α → α → Prop} {source target : α} (before : Acyclic E) :
    Acyclic (Insert E source target) ↔ ¬ Walk E target source := by
  constructor
  · intro after backPath
    exact insert_creates_cycle_if_backpath backPath after
  · exact insert_preserves_acyclic before

#print axioms insert_acyclic_iff_no_backpath

end OrdivonHostDAG
