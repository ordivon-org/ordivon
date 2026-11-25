-- Security Product Consequence Evidence, scoped to a pure model.
-- No claim about an authenticated external observation or Rego refinement.
namespace OrdivonSecurity.Consequence

structure Evidence where
  admitted : Bool
  executionBound : Bool
  claimedWorldPlane : Bool
  digestMatched : Bool
  sourceAuthenticated : Bool
  sourceIndependent : Bool
  deriving Repr

def ContentMatched (e : Evidence) : Bool :=
  e.admitted && e.executionBound && e.claimedWorldPlane && e.digestMatched

def AuthenticatedConsequence (e : Evidence) : Bool :=
  ContentMatched e && e.sourceAuthenticated && e.sourceIndependent

theorem authenticated_needs_qualified_source (e : Evidence)
    (h : AuthenticatedConsequence e = true) :
    e.sourceAuthenticated = true ∧ e.sourceIndependent = true := by
  simp [AuthenticatedConsequence, Bool.and_eq_true] at h
  exact ⟨h.1.2, h.2⟩

theorem no_authenticated_source_cannot_verify (e : Evidence)
    (h : e.sourceAuthenticated = false) :
    AuthenticatedConsequence e = false := by
  simp [AuthenticatedConsequence, h]

theorem no_independent_source_cannot_verify (e : Evidence)
    (h : e.sourceIndependent = false) :
    AuthenticatedConsequence e = false := by
  simp [AuthenticatedConsequence, h]

theorem content_match_is_insufficient :
    ∃ e : Evidence,
      ContentMatched e = true ∧ AuthenticatedConsequence e = false := by
  let witness : Evidence := {
    admitted := true
    executionBound := true
    claimedWorldPlane := true
    digestMatched := true
    sourceAuthenticated := false
    sourceIndependent := false
  }
  exact ⟨witness, by decide, by decide⟩

-- This policy currently has only caller-supplied claims. Its safe positive
-- conclusion is "CONTENT_MATCHED_UNVERIFIED", never a verification witness.
def CurrentPolicyClaimsVerified (_ : Evidence) : Bool := false

theorem no_untrusted_promotion (e : Evidence) :
    CurrentPolicyClaimsVerified e = false := rfl

end OrdivonSecurity.Consequence

#print axioms OrdivonSecurity.Consequence.authenticated_needs_qualified_source
#print axioms OrdivonSecurity.Consequence.no_authenticated_source_cannot_verify
#print axioms OrdivonSecurity.Consequence.content_match_is_insufficient
#print axioms OrdivonSecurity.Consequence.no_untrusted_promotion

-- A report delta describes observations, not the scan's actual input.
-- This independent specification assumes qualified digest/coverage facts
-- supplied by the native producer; it does not implement a scanner.
namespace OrdivonSecurity.Remediation

structure Evidence where
  beforeSbom : String
  afterSbom : String
  beforeScanned : Option String
  afterScanned : Option String
  baselinePresent : Bool
  baselineAbsentAfter : Bool
  producerAuthenticated : Bool
  comparableCoverage : Bool
  deriving Repr

def ReportDelta (e : Evidence) : Prop :=
  e.beforeSbom ≠ e.afterSbom ∧
  e.baselinePresent = true ∧ e.baselineAbsentAfter = true

def QualifiedClearance (e : Evidence) : Prop :=
  ReportDelta e ∧
  e.beforeScanned = some e.beforeSbom ∧
  e.afterScanned = some e.afterSbom ∧
  e.producerAuthenticated = true ∧ e.comparableCoverage = true

theorem unknown_after_scan_cannot_qualify (e : Evidence)
    (h : e.afterScanned = none) : ¬ QualifiedClearance e := by
  intro q
  have bound := q.2.2.1
  rw [h] at bound
  cases bound

theorem unrelated_after_scan_cannot_qualify (e : Evidence)
    (h : e.afterScanned ≠ some e.afterSbom) : ¬ QualifiedClearance e := by
  intro q
  exact h q.2.2.1

theorem incomplete_coverage_cannot_qualify (e : Evidence)
    (h : e.comparableCoverage = false) : ¬ QualifiedClearance e := by
  intro q
  have covered := q.2.2.2.2
  rw [h] at covered
  cases covered

def qualifiedExample : Evidence := {
  beforeSbom := "old"
  afterSbom := "new"
  beforeScanned := some "old"
  afterScanned := some "new"
  baselinePresent := true
  baselineAbsentAfter := true
  producerAuthenticated := true
  comparableCoverage := true
}

theorem qualified_example : QualifiedClearance qualifiedExample := by
  unfold QualifiedClearance ReportDelta qualifiedExample
  decide

theorem report_delta_with_unknown_scan_is_insufficient :
    ∃ e : Evidence, ReportDelta e ∧ ¬ QualifiedClearance e := by
  let e := { qualifiedExample with afterScanned := none }
  refine ⟨e, ?_, unknown_after_scan_cannot_qualify e rfl⟩
  unfold ReportDelta e qualifiedExample
  decide

end OrdivonSecurity.Remediation

#print axioms OrdivonSecurity.Remediation.qualified_example
#print axioms OrdivonSecurity.Remediation.report_delta_with_unknown_scan_is_insufficient
#print axioms OrdivonSecurity.Remediation.unrelated_after_scan_cannot_qualify

-- Provider readiness is not evidence of the current source cut.
-- This model classifies a synthetic observation, not authorization.
namespace OrdivonSecurity.ProviderObservation

inductive Standing where
  | unknown
  | different
  | matched
  deriving DecidableEq, Repr

structure Observation where
  healthy : Bool
  desired : String
  observed : Option String
  sameEvaluation : Bool
  sourceQualified : Bool
  deriving Repr

def classify (o : Observation) : Standing :=
  if o.sameEvaluation && o.sourceQualified then
    match o.observed with
    | none => .unknown
    | some value => if value = o.desired then .matched else .different
  else .unknown

theorem health_independent (o : Observation) (health : Bool) :
    classify { o with healthy := health } = classify o := by
  rfl

theorem missing_observation_unknown (o : Observation)
    (h : o.observed = none) : classify o = .unknown := by
  simp [classify, h]

theorem unbound_observation_unknown (o : Observation)
    (h : o.sameEvaluation = false) : classify o = .unknown := by
  simp [classify, h]

theorem unqualified_source_unknown (o : Observation)
    (h : o.sourceQualified = false) : classify o = .unknown := by
  simp [classify, h]

def healthyOld : Observation := {
  healthy := true
  desired := "new"
  observed := some "old"
  sameEvaluation := true
  sourceQualified := true
}

theorem healthy_old_not_matched : classify healthyOld = .different := by decide

theorem qualified_match_reachable :
    classify { healthyOld with observed := some "new" } = .matched := by decide

theorem same_label_without_binding_unknown :
    classify { healthyOld with observed := some "new", sameEvaluation := false }
      = .unknown := by decide

end OrdivonSecurity.ProviderObservation

#print axioms OrdivonSecurity.ProviderObservation.health_independent
#print axioms OrdivonSecurity.ProviderObservation.missing_observation_unknown
#print axioms OrdivonSecurity.ProviderObservation.unbound_observation_unknown
#print axioms OrdivonSecurity.ProviderObservation.unqualified_source_unknown
#print axioms OrdivonSecurity.ProviderObservation.healthy_old_not_matched
#print axioms OrdivonSecurity.ProviderObservation.qualified_match_reachable
#print axioms OrdivonSecurity.ProviderObservation.same_label_without_binding_unknown
