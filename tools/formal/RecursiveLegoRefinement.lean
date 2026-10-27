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


-- Pure, total mathematical readsets for R2.1 contract applicability.
-- The variables below describe a model; this theorem does NOT establish
-- which files, services, toolchains, credentials or external effects a real
-- Ordivon implementation reads. A qualified implementation-to-model bridge
-- and a complete actual readset are independent proof obligations.
namespace OrdivonR21

def SameOn {Key Value : Type} (readset : Key → Prop)
    (before after : Key → Value) : Prop :=
  ∀ key, readset key → before key = after key

def BehaviorBoundedBy {Key Value Output : Type}
    (actualReads : Key → Prop) (behavior : (Key → Value) → Output) : Prop :=
  ∀ before after, SameOn actualReads before after →
    behavior before = behavior after

-- Once a complete may-read envelope has been separately qualified, an
-- unchanged envelope is enough to reuse a PURE model result without looking
-- inside its implementation. This does not upgrade any verifier status.
theorem opaque_result_preserved_by_complete_readset
    {Key Value Output : Type}
    (actualReads declaredMayReads : Key → Prop)
    (behavior : (Key → Value) → Output)
    (complete : ∀ key, actualReads key → declaredMayReads key)
    (bounded : BehaviorBoundedBy actualReads behavior)
    (before after : Key → Value)
    (unchanged : SameOn declaredMayReads before after) :
    behavior before = behavior after := by
  apply bounded before after
  intro key hActual
  exact unchanged key (complete key hActual)

-- Any pure downstream function can consume the preserved output opaquely.
-- State changes, effects, authorization and installed identity are excluded
-- from this mathematical theorem; a concrete client must qualify them.
theorem opaque_pure_consumer_preserves_result
    {Key Value Output ConsumerOutput : Type}
    (actualReads declaredMayReads : Key → Prop)
    (producer : (Key → Value) → Output)
    (consumer : Output → ConsumerOutput)
    (complete : ∀ key, actualReads key → declaredMayReads key)
    (bounded : BehaviorBoundedBy actualReads producer)
    (before after : Key → Value)
    (unchanged : SameOn declaredMayReads before after) :
    consumer (producer before) = consumer (producer after) := by
  rw [opaque_result_preserved_by_complete_readset
    actualReads declaredMayReads producer complete bounded before after unchanged]

-- Machine-checked adversarial counterexample: the declared may-read
-- envelope fails to mention the key TRUE; two worlds agree at key FALSE,
-- yet their pure outputs differ. Hence mere "unchanged visible files"
-- cannot justify evidence reuse if a hidden dependency remains.
theorem hidden_dependency_invalidates_unqualified_reuse :
    ∃ (declaredMayReads : Bool → Prop)
      (before after : Bool → Bool)
      (behavior : (Bool → Bool) → Bool),
      SameOn declaredMayReads before after ∧
      behavior before ≠ behavior after := by
  refine ⟨(fun key => key = false), (fun key => key),
    (fun _ => false), (fun world => world true), ?_, ?_⟩
  · intro key hKey
    cases key with
    | false => rfl
    | true => cases hKey
  · decide

-- Equal carrier bytes do not assert the semantics of environments that
-- interpret the carrier. A relocation candidate is source evidence only.
theorem same_carrier_different_environment_can_change_output :
    ∃ (carrier : Bool) (oldEnv newEnv : Bool → Bool)
      (interpret : (Bool → Bool) → Bool → Bool),
      interpret oldEnv carrier ≠ interpret newEnv carrier := by
  refine ⟨true, (fun _ => false), (fun _ => true),
    (fun environment bytes => environment bytes), ?_⟩
  decide

end OrdivonR21
