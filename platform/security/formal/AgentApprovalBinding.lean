-- Agent effect-bound approval: a scoped model of the normalized Rego contract.
-- The trusted WebAuthn assertion and transaction/PEP are external obligations.
namespace OrdivonSecurity.AgentApproval

structure Effect where
  effectId : String
  effectDigest : String

structure Approval where
  verified : Bool
  effectId : String
  effectDigest : String

def Bound (a : Approval) (effect : Effect) : Prop :=
  a.verified = true ∧
  a.effectId = effect.effectId ∧
  a.effectDigest = effect.effectDigest

theorem bound_requires_exact_content (a : Approval) (effect : Effect)
    (h : Bound a effect) : a.effectDigest = effect.effectDigest :=
  h.2.2

theorem changed_content_cannot_reuse_approval (a : Approval) (effect : Effect)
    (h : a.effectDigest ≠ effect.effectDigest) : ¬ Bound a effect := by
  intro hBound
  exact h hBound.2.2

theorem same_effect_id_is_not_enough :
    ∃ a : Approval, ∃ effect : Effect,
      a.verified = true ∧ a.effectId = effect.effectId ∧
      ¬ Bound a effect := by
  let effect : Effect := { effectId := "id-1", effectDigest := "sha256:A" }
  let a : Approval := {
    verified := true
    effectId := "id-1"
    effectDigest := "sha256:B"
  }
  have hMismatch : a.effectDigest ≠ effect.effectDigest := by decide
  exact ⟨a, effect, rfl, rfl, changed_content_cannot_reuse_approval a effect hMismatch⟩

end OrdivonSecurity.AgentApproval

#print axioms OrdivonSecurity.AgentApproval.bound_requires_exact_content
#print axioms OrdivonSecurity.AgentApproval.changed_content_cannot_reuse_approval
#print axioms OrdivonSecurity.AgentApproval.same_effect_id_is_not_enough
