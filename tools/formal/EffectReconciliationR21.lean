-- This is an R2.1 scoped effect-observation contract over the existing
-- Composition C06 responsibility, not a new owner/registry/permission layer.
-- Proved statements concern this finite abstract model; concrete Python
-- refinement and external provider semantics remain separate obligations.

namespace OrdivonR21Effect

inductive NextRead where
  | observeOriginal | reconcileOriginal | verifyDomainEffect
  deriving DecidableEq, Repr

structure Input where
  terminal : Bool
  recoveryRequired : Bool
  deliveryUnknown : Bool
  reconcileState : Bool
  deriving DecidableEq, Repr

structure Output where
  nextRead : NextRead
  automaticRetryAdmissible : Bool
  providerEffectEstablished : Bool
  proofReuseAdmissible : Bool
  deriving DecidableEq, Repr

def nextRead (i : Input) : NextRead :=
  if i.recoveryRequired || i.deliveryUnknown || i.reconcileState then
    .reconcileOriginal
  else if !i.terminal then
    .observeOriginal
  else
    .verifyDomainEffect

def project (i : Input) : Output :=
  { nextRead := nextRead i
    automaticRetryAdmissible := false
    providerEffectEstablished := false
    proofReuseAdmissible := false }

theorem no_automatic_retry (i : Input) :
    (project i).automaticRetryAdmissible = false := rfl

theorem no_provider_effect_promotion (i : Input) :
    (project i).providerEffectEstablished = false := rfl

theorem no_proof_reuse_promotion (i : Input) :
    (project i).proofReuseAdmissible = false := rfl

theorem recovery_requires_reconciliation (i : Input)
    (h : i.recoveryRequired = true) :
    (project i).nextRead = .reconcileOriginal := by
  simp [project, nextRead, h]

theorem unknown_delivery_requires_reconciliation (i : Input)
    (h : i.deliveryUnknown = true) :
    (project i).nextRead = .reconcileOriginal := by
  cases hr : i.recoveryRequired <;> simp [project, nextRead, hr, h]

theorem explicit_reconcile_state_requires_reconciliation (i : Input)
    (h : i.reconcileState = true) :
    (project i).nextRead = .reconcileOriginal := by
  cases hr : i.recoveryRequired <;>
    cases hd : i.deliveryUnknown <;> simp [project, nextRead, hr, hd, h]

theorem live_uncontested_operation_requires_observation (i : Input)
    (hr : i.recoveryRequired = false) (hd : i.deliveryUnknown = false)
    (hs : i.reconcileState = false) (ht : i.terminal = false) :
    (project i).nextRead = .observeOriginal := by
  simp [project, nextRead, hr, hd, hs, ht]

theorem terminal_uncontested_operation_requires_domain_readback (i : Input)
    (hr : i.recoveryRequired = false) (hd : i.deliveryUnknown = false)
    (hs : i.reconcileState = false) (ht : i.terminal = true) :
    (project i).nextRead = .verifyDomainEffect := by
  simp [project, nextRead, hr, hd, hs, ht]

-- Nonvacuity: all three recommendations are reachable in the admitted
-- finite input universe. Constant reconciliation (or constant failure)
-- cannot satisfy the full theorem set.
theorem all_three_routes_reachable :
    (∃ i, (project i).nextRead = .reconcileOriginal) ∧
    (∃ i, (project i).nextRead = .observeOriginal) ∧
    (∃ i, (project i).nextRead = .verifyDomainEffect) := by
  constructor
  · exact ⟨⟨true, true, false, false⟩, by decide⟩
  constructor
  · exact ⟨⟨false, false, false, false⟩, by decide⟩
  · exact ⟨⟨true, false, false, false⟩, by decide⟩

-- A provider-side effect is a different state coordinate from a successful
-- process or committed delivery. Two concrete realizations can give the
-- SAME Gateway-shaped observation and different provider-side effects.
structure Realization where
  observation : Input
  processSucceeded : Bool
  deliveryCommitted : Bool
  providerEffectCompleted : Bool

theorem observation_and_process_do_not_determine_provider_effect :
    ∃ a b : Realization,
      a.observation = b.observation ∧
      a.processSucceeded = true ∧ b.processSucceeded = true ∧
      a.deliveryCommitted = true ∧ b.deliveryCommitted = true ∧
      a.providerEffectCompleted = false ∧ b.providerEffectCompleted = true := by
  let i : Input := ⟨true, false, false, false⟩
  exact ⟨⟨i, true, true, false⟩,
         ⟨i, true, true, true⟩,
         rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩


-- Emit the complete 2^4 abstract state space from the *same* kernel-checked
-- nextRead implementation. Native Python comparison checks only this bounded
-- projection, not an unrestricted Python/runtime or provider-side refinement.
def nextReadCode : NextRead → String
  | .observeOriginal => "OBSERVE_ORIGINAL_OPERATION"
  | .reconcileOriginal => "RECONCILE_ORIGINAL_OPERATION"
  | .verifyDomainEffect => "VERIFY_DOMAIN_EFFECT_WITH_OWNER"

def bit (v : Bool) : String := if v then "1" else "0"

def emitModel : IO Unit := do
  for terminal in #[false, true] do
    for recovery in #[false, true] do
      for unknown in #[false, true] do
        for reconcile in #[false, true] do
          let i : Input := ⟨terminal, recovery, unknown, reconcile⟩
          IO.println s!"{bit terminal}|{bit recovery}|{bit unknown}|{bit reconcile}|{nextReadCode (project i).nextRead}"

end OrdivonR21Effect

def main : IO Unit := OrdivonR21Effect.emitModel
