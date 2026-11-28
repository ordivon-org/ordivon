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
