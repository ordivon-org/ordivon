-- Effect admission v2: bounded Authority-Revision consistency model.
-- This proves properties of the typed admission relation, NOT that arbitrary
-- caller-supplied authorities are authenticated or that the Rego code refines
-- Lean for every JSON input. The latter requires native OPA/consumer evidence.
namespace OrdivonSecurity.EffectAuthority

structure AuthorityRead where
  requestAuthorityId : String
  recordAuthorityId : String
  requestDigest : String
  recordDigest : String
  requestDigestQualified : Bool
  recordDigestQualified : Bool
  deriving Repr

def Bound (x : AuthorityRead) : Prop :=
  x.requestAuthorityId = x.recordAuthorityId ∧
  x.requestDigest = x.recordDigest ∧
  x.requestDigestQualified = true ∧
  x.recordDigestQualified = true

theorem admitted_implies_exact_revision (x : AuthorityRead)
    (h : Bound x) : x.requestDigest = x.recordDigest := h.2.1

theorem admitted_implies_both_digests_qualified (x : AuthorityRead)
    (h : Bound x) :
    x.requestDigestQualified = true ∧ x.recordDigestQualified = true :=
  ⟨h.2.2.1, h.2.2.2⟩

theorem stale_digest_cannot_admit (x : AuthorityRead)
    (h : x.requestDigest ≠ x.recordDigest) : ¬ Bound x := by
  intro admitted
  exact h (admitted_implies_exact_revision x admitted)

theorem unqualified_digest_cannot_admit (x : AuthorityRead)
    (h : x.recordDigestQualified = false) : ¬ Bound x := by
  intro admitted
  have qualified := (admitted_implies_both_digests_qualified x admitted).2
  rw [h] at qualified
  cases qualified

-- The legacy v1 check is weaker. Equal authority IDs and valid explicit
-- digest strings do not prove that the request sees the same Authority cut.
theorem legacy_id_match_does_not_imply_bound_v2 :
    ∃ x : AuthorityRead,
      x.requestAuthorityId = x.recordAuthorityId ∧
      ¬ Bound x := by
  let x : AuthorityRead := {
    requestAuthorityId := "authority:a"
    recordAuthorityId := "authority:a"
    requestDigest := "sha256:old"
    recordDigest := "sha256:new"
    requestDigestQualified := true
    recordDigestQualified := true
  }
  have hMismatch : x.requestDigest ≠ x.recordDigest := by decide
  exact ⟨x, rfl, stale_digest_cannot_admit x hMismatch⟩

end OrdivonSecurity.EffectAuthority

#print axioms OrdivonSecurity.EffectAuthority.admitted_implies_exact_revision
#print axioms OrdivonSecurity.EffectAuthority.admitted_implies_both_digests_qualified
#print axioms OrdivonSecurity.EffectAuthority.stale_digest_cannot_admit
#print axioms OrdivonSecurity.EffectAuthority.unqualified_digest_cannot_admit
#print axioms OrdivonSecurity.EffectAuthority.legacy_id_match_does_not_imply_bound_v2
