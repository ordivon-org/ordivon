import RecursiveLegoRefinement

-- Scoped abstraction: no claim about a concrete Qwen implementation.
-- "Prompt" is an allowed external input. Intervention is an internal operation.
namespace OrdivonR21.LatentInput

structure Model (Context Prompt State Observation : Type) where
  allowed : Context → Prompt → Prop
  encode : Context → Prompt → State
  intervene : State → State
  observe : State → Observation
  safe : Context → State → Prop

def Reachable {C P H O : Type} (m : Model C P H O)
    (c : C) (target : H) : Prop :=
  ∃ p : P, m.allowed c p ∧ m.encode c p = target

def Exact {C P H O : Type} (m : Model C P H O)
    (c : C) (base : P) : Prop :=
  Reachable m c (m.intervene (m.encode c base))

def Behavioral {C P H O : Type} (m : Model C P H O)
    (c : C) (base : P) : Prop :=
  ∃ p : P, m.allowed c p ∧
    m.observe (m.encode c p) =
      m.observe (m.intervene (m.encode c base))

-- Exact state reproduction implies agreement under this particular observer.
theorem exact_implies_behavioral {C P H O : Type}
    (m : Model C P H O) (c : C) (base : P) :
    Exact m c base → Behavioral m c base := by
  rintro ⟨p, hp, heq⟩
  exact ⟨p, hp, congrArg m.observe heq⟩

-- A *separately assumed* invariant of allowed inputs excludes an
-- unsafe intervention target from the externally reachable state set.
theorem invariant_excludes_exact {C P H O : Type}
    (m : Model C P H O) (c : C) (base : P)
    (invariant : ∀ p : P, m.allowed c p → m.safe c (m.encode c p))
    (targetUnsafe : ¬ m.safe c (m.intervene (m.encode c base))) :
    ¬ Exact m c base := by
  rintro ⟨p, hp, heq⟩
  apply targetUnsafe
  rw [← heq]
  exact invariant p hp

-- Reuse the existing R2.1 assume/guarantee contract with totality,
-- rather than inventing a second verification calculus.
def safePort {C P H O : Type} (m : Model C P H O)
    (c : C) : OrdivonR21.IOContract P H where
  assume := m.allowed c
  guarantee := fun p h => h = m.encode c p ∧ m.safe c h

def ordinaryBehavior {C P H O : Type} (m : Model C P H O)
    (c : C) : P → H → Prop :=
  fun p h => h = m.encode c p

def intervenedBehavior {C P H O : Type} (m : Model C P H O)
    (c : C) : P → H → Prop :=
  fun p h => h = m.intervene (m.encode c p)

theorem ordinary_implements_safe_port {C P H O : Type}
    (m : Model C P H O) (c : C)
    (invariant : ∀ p : P, m.allowed c p → m.safe c (m.encode c p)) :
    OrdivonR21.Implements (safePort m c) (ordinaryBehavior m c) := by
  constructor
  · intro p h hp hEq
    constructor
    · exact hEq
    · rw [hEq]
      exact invariant p hp
  · intro p _
    exact ⟨m.encode c p, rfl⟩

theorem unsafe_intervention_violates_safe_port {C P H O : Type}
    (m : Model C P H O) (c : C) (base : P)
    (baseAllowed : m.allowed c base)
    (targetUnsafe : ¬ m.safe c (m.intervene (m.encode c base))) :
    ¬ OrdivonR21.Implements (safePort m c) (intervenedBehavior m c) := by
  intro hImpl
  have hg := hImpl.1 base (m.intervene (m.encode c base))
    baseAllowed rfl
  exact targetUnsafe hg.2

-- A concrete finite counterexample: all input states are "false",
-- direct intervention reaches "true"; a coarse observer cannot distinguish.
def coarse : Model Unit Unit Bool Unit where
  allowed := fun _ _ => True
  encode := fun _ _ => false
  intervene := Bool.not
  observe := fun _ => ()
  safe := fun _ h => h = false

theorem coarse_behavioral : Behavioral coarse () () := by
  exact ⟨(), trivial, rfl⟩

theorem coarse_not_exact : ¬ Exact coarse () () := by
  rintro ⟨p, _, heq⟩
  change false = true at heq
  cases heq

theorem behavioral_does_not_imply_exact :
    ∃ (C P H O : Type) (m : Model C P H O) (c : C) (base : P),
      Behavioral m c base ∧ ¬ Exact m c base := by
  exact ⟨Unit, Unit, Bool, Unit, coarse, (), (),
    coarse_behavioral, coarse_not_exact⟩

theorem coarse_target_unsafe :
    ¬ coarse.safe () (coarse.intervene (coarse.encode () ())) := by
  intro heq
  change true = false at heq
  cases heq

-- The same model and intervention can be reachable under one context
-- and unreachable under another. Context is part of the contract.
def contextModel : Model Bool Bool Bool Bool where
  allowed := fun _ _ => True
  encode := fun c p => if c then p else false
  intervene := Bool.not
  observe := id
  safe := fun _ _ => True

theorem context_sensitive_reachability :
    Exact contextModel true false ∧
    ¬ Exact contextModel false false := by
  constructor
  · refine ⟨true, trivial, ?_⟩
    rfl
  · rintro ⟨p, _, heq⟩
    change false = true at heq
    cases heq

-- Non-vacuity of the simple finite model: at least one allowed prompt,
-- the direct target is unsafe, and exact emulation is impossible.
theorem finite_countermodel_nonvacuous :
    (∃ p : Unit, coarse.allowed () p) ∧
    (¬ coarse.safe () (coarse.intervene (coarse.encode () ()))) ∧
    (¬ Exact coarse () ()) := by
  exact ⟨⟨(), trivial⟩, coarse_target_unsafe, coarse_not_exact⟩


-- R2: observer-completeness is a property-specific condition, not an
-- assertion that an output observer reconstructs the full hidden trajectory.
def SafetyObservable {C P H O : Type} (m : Model C P H O)
    (c : C) : Prop :=
  ∀ a b : H, m.observe a = m.observe b →
    (m.safe c a ↔ m.safe c b)

theorem safety_observable_iff_factors {C P H O : Type}
    (m : Model C P H O) (c : C) :
    SafetyObservable m c ↔
      ∃ q : O → Prop, ∀ h : H, m.safe c h ↔ q (m.observe h) := by
  constructor
  · intro h
    refine ⟨(fun o => ∃ x : H, m.observe x = o ∧ m.safe c x), ?_⟩
    intro x
    constructor
    · intro hx
      exact ⟨x, rfl, hx⟩
    · rintro ⟨y, hyObs, hySafe⟩
      exact (h y x hyObs).mp hySafe
  · rintro ⟨q, hq⟩ a b hObs
    constructor
    · intro ha
      apply (hq b).mpr
      rw [← hObs]
      exact (hq a).mp ha
    · intro hb
      apply (hq a).mpr
      rw [hObs]
      exact (hq b).mp hb

theorem behavioral_preserves_safe_if_observable {C P H O : Type}
    (m : Model C P H O) (c : C) (base : P)
    (hObserver : SafetyObservable m c)
    (hInvariant : ∀ p : P, m.allowed c p → m.safe c (m.encode c p)) :
    Behavioral m c base →
      m.safe c (m.intervene (m.encode c base)) := by
  rintro ⟨p, hp, hEq⟩
  exact (hObserver (m.encode c p)
    (m.intervene (m.encode c base)) hEq).mp (hInvariant p hp)

theorem injective_observer_behavioral_implies_exact {C P H O : Type}
    (m : Model C P H O) (c : C) (base : P)
    (hInjective : Function.Injective m.observe) :
    Behavioral m c base → Exact m c base := by
  rintro ⟨p, hp, hEq⟩
  exact ⟨p, hp, hInjective hEq⟩

-- Non-empty domain: an allowed state is safe and observationally equivalent
-- to an unsafe intervened state when the observer has discarded information.
theorem behavioral_can_hide_unsafe_target :
    Behavioral coarse () () ∧
    (∀ p : Unit, coarse.allowed () p →
      coarse.safe () (coarse.encode () p)) ∧
    ¬ coarse.safe () (coarse.intervene (coarse.encode () ())) := by
  refine ⟨coarse_behavioral, ?_, coarse_target_unsafe⟩
  intro _ _
  rfl

-- No changed encoder, admissibility predicate, internal operation, or safety
-- predicate is required for an observer change to invalidate equivalence.
def blindObserver : Model Unit Unit Bool Bool where
  allowed := fun _ _ => True
  encode := fun _ _ => false
  intervene := Bool.not
  observe := fun _ => false
  safe := fun _ h => h = false

def discriminatingObserver : Model Unit Unit Bool Bool where
  allowed := fun _ _ => True
  encode := fun _ _ => false
  intervene := Bool.not
  observe := id
  safe := fun _ h => h = false

theorem observer_change_invalidates_behavioral :
    Behavioral blindObserver () () ∧
    ¬ Behavioral discriminatingObserver () () := by
  constructor
  · exact ⟨(), trivial, rfl⟩
  · rintro ⟨_, _, heq⟩
    change false = true at heq
    cases heq

-- Exactly the relevant predicates/functions are required for transport.
-- An irrelevant environment change does not invalidate the conclusion.
theorem exact_reachability_transport {C P H O : Type}
    (old new : Model C P H O) (c : C) (base : P)
    (allowedStable : ∀ p : P, old.allowed c p ↔ new.allowed c p)
    (reachableStatesStable : ∀ p : P, old.allowed c p →
      old.encode c p = new.encode c p)
    (targetStable :
      old.intervene (old.encode c base) =
      new.intervene (new.encode c base)) :
    Exact old c base ↔ Exact new c base := by
  constructor
  · rintro ⟨p, hp, heq⟩
    refine ⟨p, (allowedStable p).mp hp, ?_⟩
    calc
      new.encode c p = old.encode c p := (reachableStatesStable p hp).symm
      _ = old.intervene (old.encode c base) := heq
      _ = new.intervene (new.encode c base) := targetStable
  · rintro ⟨p, hp, heq⟩
    have ho : old.allowed c p := (allowedStable p).mpr hp
    refine ⟨p, ho, ?_⟩
    calc
      old.encode c p = new.encode c p := reachableStatesStable p ho
      _ = new.intervene (new.encode c base) := heq
      _ = old.intervene (old.encode c base) := targetStable.symm

theorem behavioral_transport {C P H O : Type}
    (old new : Model C P H O) (c : C) (base : P)
    (allowedStable : ∀ p : P, old.allowed c p ↔ new.allowed c p)
    (observedStatesStable : ∀ p : P, old.allowed c p →
      old.observe (old.encode c p) = new.observe (new.encode c p))
    (observedTargetStable :
      old.observe (old.intervene (old.encode c base)) =
      new.observe (new.intervene (new.encode c base))) :
    Behavioral old c base ↔ Behavioral new c base := by
  constructor
  · rintro ⟨p, hp, heq⟩
    refine ⟨p, (allowedStable p).mp hp, ?_⟩
    calc
      new.observe (new.encode c p) = old.observe (old.encode c p) :=
        (observedStatesStable p hp).symm
      _ = old.observe (old.intervene (old.encode c base)) := heq
      _ = new.observe (new.intervene (new.encode c base)) :=
        observedTargetStable
  · rintro ⟨p, hp, heq⟩
    have ho : old.allowed c p := (allowedStable p).mpr hp
    refine ⟨p, ho, ?_⟩
    calc
      old.observe (old.encode c p) = new.observe (new.encode c p) :=
        observedStatesStable p ho
      _ = new.observe (new.intervene (new.encode c base)) := heq
      _ = old.observe (old.intervene (old.encode c base)) :=
        observedTargetStable.symm

-- Safe inputs are preserved across a change only if every affected
-- admissible state keeps its safety truth value.
theorem input_invariant_transport {C P H O : Type}
    (old new : Model C P H O) (c : C)
    (allowedStable : ∀ p : P, old.allowed c p ↔ new.allowed c p)
    (reachableSafetyStable : ∀ p : P, old.allowed c p →
      (old.safe c (old.encode c p) ↔
       new.safe c (new.encode c p))) :
    (∀ p : P, old.allowed c p → old.safe c (old.encode c p)) ↔
    (∀ p : P, new.allowed c p → new.safe c (new.encode c p)) := by
  constructor
  · intro h p hp
    have ho := (allowedStable p).mpr hp
    exact (reachableSafetyStable p ho).mp (h p ho)
  · intro h p hp
    exact (reachableSafetyStable p hp).mpr (h p ((allowedStable p).mp hp))

-- Correspondence between an abstract mathematical model and an executable
-- implementation is an explicit premise. No proof checker can infer it
-- from the existence of the abstract theorem alone.
theorem simulation_transfers_input_invariant
    {C P Abstract Concrete OA OC : Type}
    (a : Model C P Abstract OA) (r : Model C P Concrete OC)
    (c : C) (relation : Abstract → Concrete → Prop)
    (admissibleSim : ∀ p : P, r.allowed c p → a.allowed c p)
    (stepSim : ∀ p : P, r.allowed c p →
      relation (a.encode c p) (r.encode c p))
    (safeSim : ∀ x y, relation x y → a.safe c x → r.safe c y)
    (provedAbstract : ∀ p : P, a.allowed c p →
      a.safe c (a.encode c p)) :
    ∀ p : P, r.allowed c p → r.safe c (r.encode c p) := by
  intro p hp
  exact safeSim _ _ (stepSim p hp)
    (provedAbstract p (admissibleSim p hp))

-- Countermodel: even if the abstract and concrete observers agree for
-- every prompt, different hidden states can violate a safety requirement.
def concreteUnsafe : Model Unit Unit Bool Unit where
  allowed := fun _ _ => True
  encode := fun _ _ => true
  intervene := id
  observe := fun _ => ()
  safe := fun _ h => h = false

theorem abstract_proof_does_not_prove_concrete :
    (∀ p : Unit, coarse.allowed () p →
      coarse.safe () (coarse.encode () p)) ∧
    (∀ p : Unit, coarse.observe (coarse.encode () p) =
      concreteUnsafe.observe (concreteUnsafe.encode () p)) ∧
    ¬ (∀ p : Unit, concreteUnsafe.allowed () p →
      concreteUnsafe.safe () (concreteUnsafe.encode () p)) := by
  constructor
  · intro _ _
    rfl
  constructor
  · intro _
    rfl
  · intro h
    have absurd := h () trivial
    change true = false at absurd
    cases absurd


-- R3: bounded and unbounded reasoning about a token-indexed trajectory.
-- A trace is a mathematical function Nat -> State, not a claim that a
-- concrete model has been instrumented or a stochastic path was measured.
structure TransitionSystem (Context State : Type) where
  initial : Context → State → Prop
  transition : Context → State → State → Prop
  safe : Context → State → Prop

def ValidTrace {C H : Type} (d : TransitionSystem C H)
    (c : C) (states : Nat → H) : Prop :=
  d.initial c (states 0) ∧
    ∀ t : Nat, d.transition c (states t) (states (t + 1))

-- Finite-prefix and global safety follow from the *explicit*
-- initial and step-invariant premises, not from a safe first token alone.
theorem trace_safety_induction {C H : Type}
    (d : TransitionSystem C H) (c : C) (states : Nat → H)
    (traceValid : ValidTrace d c states)
    (initialSafe : ∀ x, d.initial c x → d.safe c x)
    (stepSafe : ∀ x y, d.safe c x →
      d.transition c x y → d.safe c y) :
    ∀ t, d.safe c (states t) := by
  intro t
  induction t with
  | zero =>
    exact initialSafe _ traceValid.1
  | succ k ih =>
    change d.safe c (states (k + 1))
    exact stepSafe _ _ ih (traceValid.2 k)

-- Incremental revalidation needs equality of predicates on the ACTUAL
-- trace positions, not equivalence of all transitions in the state space.
theorem valid_trace_transport_on_path {C H : Type}
    (old new : TransitionSystem C H) (c : C) (states : Nat → H)
    (initialPreserved :
      old.initial c (states 0) ↔ new.initial c (states 0))
    (transitionsPreserved : ∀ t,
      old.transition c (states t) (states (t + 1)) ↔
      new.transition c (states t) (states (t + 1))) :
    ValidTrace old c states ↔ ValidTrace new c states := by
  constructor
  · intro valid
    exact ⟨initialPreserved.mp valid.1,
      fun t => (transitionsPreserved t).mp (valid.2 t)⟩
  · intro valid
    exact ⟨initialPreserved.mpr valid.1,
      fun t => (transitionsPreserved t).mpr (valid.2 t)⟩

theorem trace_safety_transport_on_path {C H : Type}
    (old new : TransitionSystem C H) (c : C) (states : Nat → H)
    (propertiesPreserved : ∀ t,
      old.safe c (states t) ↔ new.safe c (states t)) :
    (∀ t, old.safe c (states t)) ↔
    (∀ t, new.safe c (states t)) := by
  constructor
  · intro h t
    exact (propertiesPreserved t).mp (h t)
  · intro h t
    exact (propertiesPreserved t).mpr (h t)

-- To carry a claim from abstract to concrete executions, an independent
-- step simulation is required for every step of the paired runs.
theorem trace_relation_by_simulation
    {C A B : Type}
    (abstract : TransitionSystem C A) (concrete : TransitionSystem C B)
    (c : C) (a : Nat → A) (b : Nat → B) (relation : A → B → Prop)
    (aRun : ValidTrace abstract c a)
    (bRun : ValidTrace concrete c b)
    (initialRelated : relation (a 0) (b 0))
    (stepRelated : ∀ x x' y y', relation x y →
      abstract.transition c x x' →
      concrete.transition c y y' →
      relation x' y') :
    ∀ t, relation (a t) (b t) := by
  intro t
  induction t with
  | zero =>
    exact initialRelated
  | succ k ih =>
    change relation (a (k + 1)) (b (k + 1))
    exact stepRelated _ _ _ _ ih (aRun.2 k) (bRun.2 k)

theorem trace_safety_by_simulation
    {C A B : Type}
    (abstract : TransitionSystem C A) (concrete : TransitionSystem C B)
    (c : C) (a : Nat → A) (b : Nat → B) (relation : A → B → Prop)
    (aRun : ValidTrace abstract c a)
    (bRun : ValidTrace concrete c b)
    (initialRelated : relation (a 0) (b 0))
    (stepRelated : ∀ x x' y y', relation x y →
      abstract.transition c x x' →
      concrete.transition c y y' →
      relation x' y')
    (safeRelated : ∀ x y, relation x y →
      abstract.safe c x → concrete.safe c y)
    (abstractSafe : ∀ t, abstract.safe c (a t)) :
    ∀ t, concrete.safe c (b t) := by
  have related := trace_relation_by_simulation
    abstract concrete c a b relation aRun bRun
    initialRelated stepRelated
  intro t
  exact safeRelated _ _ (related t) (abstractSafe t)

-- The observer may report identical outputs at EVERY token position,
-- yet the underlying safety predicate can differ at EVERY position.
theorem equal_observed_traces_do_not_imply_safety :
    ∃ (a b : Nat → Bool),
      (∀ t, (fun _ : Bool => ()) (a t) =
        (fun _ : Bool => ()) (b t)) ∧
      (∀ t, a t = false) ∧
      ¬ (∀ t, b t = false) := by
  refine ⟨(fun _ => false), (fun _ => true), ?_, ?_, ?_⟩
  · intro _
    rfl
  · intro _
    rfl
  · intro h
    have impossible : true = false := h 0
    cases impossible

-- An allowed, valid transition can move from a safe first state into
-- an unsafe second state when inductive-step preservation is absent.
theorem safe_initial_does_not_imply_trace_safety :
    ∃ (d : TransitionSystem Unit Bool) (states : Nat → Bool),
      ValidTrace d () states ∧
      d.safe () (states 0) ∧
      ¬ d.safe () (states 1) := by
  let d : TransitionSystem Unit Bool := {
    initial := fun _ x => x = false
    transition := fun _ _ _ => True
    safe := fun _ x => x = false
  }
  let states : Nat → Bool := fun n =>
    match n with
    | 0 => false
    | _ + 1 => true
  refine ⟨d, states, ?_, ?_, ?_⟩
  · constructor
    · rfl
    · intro _
      trivial
  · rfl
  · intro h
    have impossible : true = false := h
    cases impossible


-- R4: nondeterministic reachability, quantifying over every concrete
-- successor, instead of assuming a preselected synchronized trajectory.
inductive NondetReachable {C H : Type} (d : TransitionSystem C H)
    (c : C) : Nat → H → Prop where
  | initial (h : H) (hInit : d.initial c h) :
      NondetReachable d c 0 h
  | next {t : Nat} {h h' : H}
      (r : NondetReachable d c t h)
      (step : d.transition c h h') :
      NondetReachable d c (t + 1) h'

-- This induction proves a property for every possible finite
-- nondeterministic path; no fairness, scheduler or choice probabilities.
theorem nondet_all_reachable_safe {C H : Type}
    (d : TransitionSystem C H) (c : C)
    (hInit : ∀ x, d.initial c x → d.safe c x)
    (hStep : ∀ x y, d.safe c x →
      d.transition c x y → d.safe c y) :
    ∀ t h, NondetReachable d c t h → d.safe c h := by
  intro t h reach
  induction reach with
  | initial h hi =>
    exact hInit h hi
  | next prev transition ih =>
    exact hStep _ _ ih transition

-- Forward simulation needs an abstract successor for each concrete
-- transition. This replaces the overly strong paired-step universal
-- relation of R3, and does not require deterministic decoding.
def ForwardSimulation {C A B : Type}
    (a : TransitionSystem C A) (b : TransitionSystem C B)
    (c : C) (relation : A → B → Prop) : Prop :=
  (∀ y, b.initial c y →
    ∃ x, a.initial c x ∧ relation x y) ∧
  (∀ x y y', relation x y → b.transition c y y' →
    ∃ x', a.transition c x x' ∧ relation x' y')

theorem nondet_forward_simulation_preserves_reachability
    {C A B : Type}
    (a : TransitionSystem C A) (b : TransitionSystem C B)
    (c : C) (relation : A → B → Prop)
    (simulation : ForwardSimulation a b c relation) :
    ∀ t y, NondetReachable b c t y →
      ∃ x, NondetReachable a c t x ∧ relation x y := by
  intro t y reach
  induction reach with
  | initial y hi =>
    obtain ⟨x, hInit, hr⟩ := simulation.1 y hi
    exact ⟨x, NondetReachable.initial x hInit, hr⟩
  | next stepBase concreteStep ih =>
    obtain ⟨x, hx, hr⟩ := ih
    obtain ⟨x', hStep, hr'⟩ :=
      simulation.2 x _ _ hr concreteStep
    exact ⟨x', NondetReachable.next hx hStep, hr'⟩

theorem nondet_forward_simulation_preserves_safety
    {C A B : Type}
    (a : TransitionSystem C A) (b : TransitionSystem C B)
    (c : C) (relation : A → B → Prop)
    (simulation : ForwardSimulation a b c relation)
    (abstractSafe : ∀ t x, NondetReachable a c t x →
      a.safe c x)
    (propertyReflects : ∀ x y, relation x y →
      a.safe c x → b.safe c y) :
    ∀ t y, NondetReachable b c t y → b.safe c y := by
  intro t y hy
  obtain ⟨x, hx, hr⟩ :=
    nondet_forward_simulation_preserves_reachability
      a b c relation simulation t y hy
  exact propertyReflects x y hr (abstractSafe t x hx)

-- A nonempty reachable system can have an unsafe nondeterministic
-- successor, so a safe initial state is not a universal trace proof.
theorem nondet_safe_start_is_insufficient :
    ∃ (d : TransitionSystem Unit Bool),
      (∀ h, d.initial () h → d.safe () h) ∧
      (∃ h, NondetReachable d () 1 h ∧ ¬ d.safe () h) := by
  let d : TransitionSystem Unit Bool := {
    initial := fun _ h => h = false
    transition := fun _ _ _ => True
    safe := fun _ h => h = false
  }
  refine ⟨d, ?_, ?_⟩
  · intro h hi
    exact hi
  · refine ⟨true, ?_, ?_⟩
    · exact NondetReachable.next
        (NondetReachable.initial false rfl) trivial
    · intro h
      have absurd : true = false := h
      cases absurd

-- A normalized binary finite-mass model represents exactly the rational
-- chance unsafeWeight / total, without requiring floating-point or making
-- claims about an installed neural sampler.
structure BinaryFiniteMass where
  safeWeight : Nat
  unsafeWeight : Nat
  total : Nat
  normalized : safeWeight + unsafeWeight = total
  nonempty : 0 < total

def RiskAtMost (mass : BinaryFiniteMass)
    (numerator denominator : Nat) : Prop :=
  0 < denominator ∧
    mass.unsafeWeight * denominator ≤ numerator * mass.total

-- Zero risk has meaning only for a normalized distribution with positive
-- denominator and total; equivalently no mass on an unsafe outcome.
theorem binary_zero_risk_iff_no_unsafe_mass
    (mass : BinaryFiniteMass) :
    RiskAtMost mass 0 1 ↔ mass.unsafeWeight = 0 := by
  unfold RiskAtMost
  constructor
  · intro ⟨_, h⟩
    rw [Nat.mul_one, Nat.zero_mul] at h
    exact Nat.le_zero.mp h
  · intro h
    constructor
    · exact Nat.zero_lt_succ 0
    · rw [h, Nat.zero_mul, Nat.zero_mul]
      exact Nat.le_refl 0

theorem binary_safe_support_implies_any_nonnegative_budget
    (mass : BinaryFiniteMass) (num den : Nat)
    (denPositive : 0 < den)
    (allSafe : mass.unsafeWeight = 0) :
    RiskAtMost mass num den := by
  constructor
  · exact denPositive
  · change mass.unsafeWeight * den ≤ num * mass.total
    rw [allSafe, Nat.zero_mul]
    exact Nat.zero_le _

-- Exact normalized nonzero risk: half of the mass is unsafe, so a zero
-- bound is mathematically false despite possible safe observations.
def halfUnsafe : BinaryFiniteMass where
  safeWeight := 1
  unsafeWeight := 1
  total := 2
  normalized := by decide
  nonempty := by decide

theorem half_unsafe_refutes_zero_risk :
    ¬ RiskAtMost halfUnsafe 0 1 := by
  intro h
  have hz := (binary_zero_risk_iff_no_unsafe_mass halfUnsafe).mp h
  have impossible : (1 : Nat) = 0 := hz
  cases impossible

theorem half_unsafe_at_most_half :
    RiskAtMost halfUnsafe 1 2 := by
  constructor
  · decide
  · decide

-- A conclusion at an exact bound requires risk-weight arithmetic, not a
-- claim that 'some safe output was sampled'.
theorem positive_unsafe_weight_invalidates_zero_budget
    (mass : BinaryFiniteMass) (unsafePositive : 0 < mass.unsafeWeight) :
    ¬ RiskAtMost mass 0 1 := by
  intro h
  have hz := (binary_zero_risk_iff_no_unsafe_mass mass).mp h
  have impossible : 0 < (0 : Nat) := by
    rw [hz] at unsafePositive
    exact unsafePositive
  exact Nat.lt_irrefl 0 impossible


-- Relating a finite probability carrier to a transition system requires
-- a sound support bridge: a positive unsafe weight must correspond to a
-- genuine transition to the state whose safety is denied.
theorem step_invariant_plus_sound_support_implies_zero_risk
    {C : Type}
    (d : TransitionSystem C Bool) (c : C)
    (mass : BinaryFiniteMass)
    (initialSafe : d.safe c false)
    (stepSafe : ∀ x y, d.safe c x →
      d.transition c x y → d.safe c y)
    (unsafeIsUnsafe : ¬ d.safe c true)
    (soundSupport : 0 < mass.unsafeWeight →
      d.transition c false true) :
    RiskAtMost mass 0 1 := by
  apply (binary_zero_risk_iff_no_unsafe_mass mass).mpr
  by_cases zero : mass.unsafeWeight = 0
  · exact zero
  · have positive : 0 < mass.unsafeWeight :=
      Nat.pos_of_ne_zero zero
    have contradicted := stepSafe false true initialSafe
      (soundSupport positive)
    exact False.elim (unsafeIsUnsafe contradicted)

-- Risk zero over a probability support is weaker than pathwise safety
-- when a valid but weight-zero transition is retained in the relation.
def zeroUnsafeMass : BinaryFiniteMass where
  safeWeight := 1
  unsafeWeight := 0
  total := 1
  normalized := by decide
  nonempty := by decide

theorem zero_probability_unsafe_branch_still_breaks_pathwise_safety :
    ∃ (d : TransitionSystem Unit Bool),
      RiskAtMost zeroUnsafeMass 0 1 ∧
      d.safe () false ∧
      d.transition () false true ∧
      ¬ d.safe () true := by
  let d : TransitionSystem Unit Bool := {
    initial := fun _ x => x = false
    transition := fun _ _ _ => True
    safe := fun _ x => x = false
  }
  refine ⟨d, ?_, ?_, ?_, ?_⟩
  · exact (binary_zero_risk_iff_no_unsafe_mass zeroUnsafeMass).mpr rfl
  · rfl
  · trivial
  · intro h
    have impossible : true = false := h
    cases impossible

end OrdivonR21.LatentInput
