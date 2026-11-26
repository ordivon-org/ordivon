-- Closed-input build qualification (an optional profile, not a universal
-- requirement for every build). This independent model states evidence
-- obligations over qualified observations, not a proof of cryptography, OS
-- isolation, Python refinement, or the artifact's business correctness.
namespace OrdivonSecurity.BuildEvidence

abbrev InputIdentity := String × String

structure Evidence where
  claimedRevision : String
  observedRevision : Option String
  capturedSourceDigest : Option String
  sourceObjectDigest : Option String
  declaredInputs : List InputIdentity
  observedReads : Option (List InputIdentity)
  completeReadWitness : Bool
  inputsProtected : Bool
  claimedArtifactDigest : String
  observedArtifactDigest : Option String
  receiverArtifactDigest : Option String
  producerAuthenticated : Bool
  receiverIndependent : Bool
  deriving Repr

def SourceBound (e : Evidence) : Prop :=
  e.observedRevision = some e.claimedRevision ∧
  ∃ digest : String,
    e.capturedSourceDigest = some digest ∧ e.sourceObjectDigest = some digest

def InputsBound (e : Evidence) : Prop :=
  SourceBound e ∧
  e.completeReadWitness = true ∧ e.inputsProtected = true ∧
  ∃ reads : List InputIdentity,
    e.observedReads = some reads ∧ ∀ read ∈ reads, read ∈ e.declaredInputs

def ContentBound (e : Evidence) : Prop :=
  e.observedArtifactDigest = some e.claimedArtifactDigest

def QualifiedClosedBuild (e : Evidence) : Prop :=
  InputsBound e ∧ ContentBound e ∧ e.producerAuthenticated = true ∧
  e.receiverIndependent = true ∧
  e.receiverArtifactDigest = some e.claimedArtifactDigest

theorem qualified_needs_exact_source (e : Evidence)
    (h : QualifiedClosedBuild e) : SourceBound e := h.1.1

theorem unknown_source_cannot_qualify (e : Evidence)
    (h : e.sourceObjectDigest = none) : ¬ QualifiedClosedBuild e := by
  intro q
  obtain ⟨_, digest, _, source⟩ := qualified_needs_exact_source e q
  rw [h] at source
  cases source

theorem mismatched_capture_cannot_qualify (e : Evidence)
    (h : e.capturedSourceDigest ≠ e.sourceObjectDigest) :
    ¬ QualifiedClosedBuild e := by
  intro q
  obtain ⟨_, digest, captured, source⟩ := qualified_needs_exact_source e q
  exact h (captured.trans source.symm)

theorem unknown_reads_cannot_qualify (e : Evidence)
    (h : e.observedReads = none) : ¬ QualifiedClosedBuild e := by
  intro q
  obtain ⟨reads, observed, _⟩ := q.1.2.2.2
  rw [h] at observed
  cases observed

theorem undeclared_read_cannot_qualify (e : Evidence) (reads : List InputIdentity)
    (r : InputIdentity) (observed : e.observedReads = some reads)
    (present : r ∈ reads) (undeclared : r ∉ e.declaredInputs) :
    ¬ QualifiedClosedBuild e := by
  intro q
  obtain ⟨actual, bound, included⟩ := q.1.2.2.2
  have same : actual = reads := Option.some.inj (bound.symm.trans observed)
  subst actual
  exact undeclared (included r present)

theorem unprotected_inputs_cannot_qualify (e : Evidence)
    (h : e.inputsProtected = false) : ¬ QualifiedClosedBuild e := by
  intro q
  have protection := q.1.2.2.1
  rw [h] at protection
  cases protection

theorem incomplete_witness_cannot_qualify (e : Evidence)
    (h : e.completeReadWitness = false) : ¬ QualifiedClosedBuild e := by
  intro q
  have complete := q.1.2.1
  rw [h] at complete
  cases complete

theorem unauthenticated_producer_cannot_qualify (e : Evidence)
    (h : e.producerAuthenticated = false) : ¬ QualifiedClosedBuild e := by
  intro q
  have authenticated := q.2.2.1
  rw [h] at authenticated
  cases authenticated

theorem nonindependent_receiver_cannot_qualify (e : Evidence)
    (h : e.receiverIndependent = false) : ¬ QualifiedClosedBuild e := by
  intro q
  have independent := q.2.2.2.1
  rw [h] at independent
  cases independent

theorem receiver_mismatch_cannot_qualify (e : Evidence)
    (h : e.receiverArtifactDigest ≠ some e.claimedArtifactDigest) :
    ¬ QualifiedClosedBuild e := by
  intro q
  exact h q.2.2.2.2

-- A positive model and its deliberately incomplete counterpart demonstrate
-- that content/signature claims are not a substitute for complete inputs.
def qualifiedExample : Evidence := {
  claimedRevision := "commit"
  observedRevision := some "commit"
  capturedSourceDigest := some "source"
  sourceObjectDigest := some "source"
  declaredInputs := [("source", "source"), ("optional", "digest")]
  observedReads := some [("source", "source")]
  completeReadWitness := true
  inputsProtected := true
  claimedArtifactDigest := "artifact"
  observedArtifactDigest := some "artifact"
  receiverArtifactDigest := some "artifact"
  producerAuthenticated := true
  receiverIndependent := true
}

theorem qualified_example : QualifiedClosedBuild qualifiedExample := by
  refine ⟨⟨⟨rfl, "source", rfl, rfl⟩, rfl, rfl, ?_⟩, rfl, rfl, rfl, rfl⟩
  refine ⟨[("source", "source")], rfl, ?_⟩
  intro r present
  simp [qualifiedExample] at present ⊢
  exact Or.inl present

theorem signed_content_without_read_witness_is_insufficient :
    ∃ e : Evidence, ContentBound e ∧ e.producerAuthenticated = true ∧
      ¬ QualifiedClosedBuild e := by
  let e := { qualifiedExample with observedReads := none }
  exact ⟨e, rfl, rfl, unknown_reads_cannot_qualify e rfl⟩

end OrdivonSecurity.BuildEvidence

#print axioms OrdivonSecurity.BuildEvidence.qualified_example
#print axioms OrdivonSecurity.BuildEvidence.mismatched_capture_cannot_qualify
#print axioms OrdivonSecurity.BuildEvidence.undeclared_read_cannot_qualify
#print axioms OrdivonSecurity.BuildEvidence.signed_content_without_read_witness_is_insufficient
