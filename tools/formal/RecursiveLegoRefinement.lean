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
def GoalDependsOnlyOn {α ρ : Type} (readset : α → ρ)
    (goal : α → Prop) : Prop :=
  ∀ before after, readset before = readset after →
    (goal before ↔ goal after)

theorem reuse_if_readset_covers_goal {α ρ : Type}
    (readset : α → ρ) (goal : α → Prop)
    (hClosed : GoalDependsOnlyOn readset goal)
    (before after : α)
    (hSame : readset before = readset after)
    (hVerified : goal before) : goal after :=
  (hClosed before after hSame).mp hVerified

-- Adding a needed dependency to the readset cannot weaken soundness.
-- The reverse (discarding dependencies) is NOT generally valid.
theorem extending_qualified_readset_preserves_soundness {α ρ δ : Type}
    (readset : α → ρ) (extra : α → δ) (goal : α → Prop)
    (hClosed : GoalDependsOnlyOn readset goal) :
    GoalDependsOnlyOn (fun x => (readset x, extra x)) goal := by
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
    ¬ GoalDependsOnlyOn
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
    GoalDependsOnlyOn
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

-- Conservative transport projection for the currently deployed Repo
-- --agent-impact algorithm. This is a theorem about *model rows* only;
-- Git readset closure, dynamic consumers, source-to-code simulation and
-- installation are intentionally NOT assumed or proved.
def compactSourceImpact {α : Type} (standing : α → String)
    (rows : List α) : List α :=
  rows.filter (fun row => standing row != "NO_DECLARED_HIT")

theorem compact_iff_non_nohit {α : Type} (standing : α → String)
    (rows : List α) (row : α) :
    row ∈ compactSourceImpact standing rows ↔
      row ∈ rows ∧ standing row ≠ "NO_DECLARED_HIT" := by
  simp [compactSourceImpact]

theorem compact_keeps_unknown {α : Type} (standing : α → String)
    (rows : List α) (row : α)
    (hMem : row ∈ rows)
    (hUnknown : standing row = "UNKNOWN") :
    row ∈ compactSourceImpact standing rows := by
  apply (compact_iff_non_nohit standing rows row).2
  constructor
  · exact hMem
  · simp [hUnknown]

theorem compact_keeps_arbitrary_future_standing {α : Type}
    (standing : α → String) (rows : List α) (row : α)
    (hMem : row ∈ rows)
    (hNotNoHit : standing row ≠ "NO_DECLARED_HIT") :
    row ∈ compactSourceImpact standing rows :=
  (compact_iff_non_nohit standing rows row).2 ⟨hMem, hNotNoHit⟩

-- Falsifies the tempting but invalid implication:
-- an absent *declared* dependency does not establish that an external
-- dynamic consumer or environment assumption remained unchanged.
theorem no_declared_hit_does_not_imply_no_external_change :
    ¬ (∀ (standing : String) (externalChanged : Bool),
        standing = "NO_DECLARED_HIT" → externalChanged = false) := by
  intro h
  have bad : true = false := h "NO_DECLARED_HIT" true rfl
  cases bad

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

-- A formal counterexample to upgrading reported approval into proof.
-- Two worlds have IDENTICAL declared verifier status but different underlying
-- truth. Therefore no decision function reading only that report can be both
-- sound and complete for the actual claim. This is source-level epistemic
-- limitation, not a proof that any production verifier is malicious.
namespace OrdivonR21

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

end OrdivonR21
