-- Abstract finite Justification AND/OR soundness for Host Agent evidence consumption.
-- GitHub Owner identity, native Git SourceCut, readset closure and Host CAS are
-- separate executable qualification obligations, NOT proved by these theorems.
-- No bespoke theorem prover, no axioms or trusted caller "verified" flag.

universe u

namespace OrdivonJustification

def AllMatched {α : Type u} (ownerMatched : α → Prop) (required : List α) : Prop :=
  ∀ evidence, evidence ∈ required → ownerMatched evidence

def Supported {α : Type u} (ownerMatched : α → Prop)
    (alternativePaths : List (List α)) : Prop :=
  ∃ path, path ∈ alternativePaths ∧ AllMatched ownerMatched path

-- A contract is supported only if there is an actual matched alternative,
-- and that alternative's *every* evidence dependency is matched by its Owner.
theorem support_sound {α : Type u} {ownerOk : α → Prop}
    {paths : List (List α)} (h : Supported ownerOk paths) :
    ∃ path, path ∈ paths ∧ ∀ e, e ∈ path → ownerOk e := by
  exact h

-- An independently sufficient alternative may survive invalidation of a
-- different path. Never infer P is false from one failed Owner check.
theorem alternative_suffices {α : Type u} {ownerOk : α → Prop}
    {paths : List (List α)} {path : List α}
    (included : path ∈ paths) (allValid : AllMatched ownerOk path) :
    Supported ownerOk paths := by
  exact ⟨path, included, allValid⟩

-- A candidate cannot be accepted when every path contains at least one
-- unmatched leaf; UNKNOWN cannot be upgraded merely because a ref exists.
theorem no_support_if_each_path_has_unmatched {α : Type u}
    {ownerOk : α → Prop} {paths : List (List α)}
    (someMissing : ∀ p, p ∈ paths → ∃ e, e ∈ p ∧ ¬ ownerOk e) :
    ¬ Supported ownerOk paths := by
  intro supported
  obtain ⟨p, present, allMatched⟩ := supported
  obtain ⟨e, member, missing⟩ := someMissing p present
  exact missing (allMatched e member)

-- Recording additional matching evidence cannot retract an already valid
-- justification. The converse is intentionally NOT assumed.
theorem support_monotone_for_added_matching_evidence {α : Type u}
    {before after : α → Prop} {paths : List (List α)}
    (inclusion : ∀ evidence, before evidence → after evidence)
    (existing : Supported before paths) :
    Supported after paths := by
  obtain ⟨path, present, allValid⟩ := existing
  exact ⟨path, present, fun e member => inclusion e (allValid e member)⟩

-- An empty OR expression has no supporting path. The implementation rejects
-- empty contracts as a conservative admission rule.
theorem no_support_from_zero_paths {α : Type u} (ownerOk : α → Prop) :
    ¬ Supported ownerOk ([] : List (List α)) := by
  intro supported
  obtain ⟨path, member, _⟩ := supported
  cases member

#print axioms support_sound
#print axioms alternative_suffices
#print axioms no_support_if_each_path_has_unmatched
#print axioms support_monotone_for_added_matching_evidence
#print axioms no_support_from_zero_paths


-- R5: distinct evidence-workflow success, incremental impact and DOMAIN proof.
-- C04 only knows a scheduling/impact standing, never a Domain acceptance.
inductive ImpactStanding where
  | recheck | unknown | reuseCandidate
  deriving DecidableEq

inductive WorkflowStanding where
  | matched | unknown
  deriving DecidableEq

inductive AgentNext where
  | lookupOwner
  | qualifyChangedDomain
  | qualifyUnknownReadset
  | qualifyCandidateDomain
  deriving DecidableEq

def decideAgent (workflow : WorkflowStanding) (impact : ImpactStanding) : AgentNext :=
  match workflow, impact with
  | .unknown, _ => .lookupOwner
  | .matched, .recheck => .qualifyChangedDomain
  | .matched, .unknown => .qualifyUnknownReadset
  | .matched, .reuseCandidate => .qualifyCandidateDomain

-- Provenance/readset closure and Domain Owner proof are separate conditions
-- beyond a matching workflow and beyond C04 source selection.
def DomainReuseAllowed (workflowMatched readsetOwnerClosed domainOwnerAccepted : Bool) : Bool :=
  workflowMatched && readsetOwnerClosed && domainOwnerAccepted

theorem no_domain_reuse_without_closed_owner_readset
    (workflowMatched domainOwnerAccepted : Bool) :
    DomainReuseAllowed workflowMatched false domainOwnerAccepted = false := by
  cases workflowMatched <;> cases domainOwnerAccepted <;> rfl

theorem no_domain_reuse_without_domain_owner_proof
    (workflowMatched readsetOwnerClosed : Bool) :
    DomainReuseAllowed workflowMatched readsetOwnerClosed false = false := by
  cases workflowMatched <;> cases readsetOwnerClosed <;> rfl

theorem domain_reuse_requires_all_three
    (workflowMatched readsetOwnerClosed domainOwnerAccepted : Bool)
    (h : DomainReuseAllowed workflowMatched readsetOwnerClosed domainOwnerAccepted = true) :
    workflowMatched = true ∧ readsetOwnerClosed = true ∧ domainOwnerAccepted = true := by
  cases workflowMatched with
  | false =>
      cases readsetOwnerClosed <;> cases domainOwnerAccepted <;> cases h
  | true =>
      cases readsetOwnerClosed with
      | false => cases domainOwnerAccepted <;> cases h
      | true =>
          cases domainOwnerAccepted with
          | false => cases h
          | true => exact ⟨rfl, rfl, rfl⟩

theorem matching_workflow_plus_changed_source_requests_domain_qualification :
    decideAgent .matched .recheck = .qualifyChangedDomain := by
  rfl

theorem matching_workflow_plus_unknown_impact_requests_readset_qualification :
    decideAgent .matched .unknown = .qualifyUnknownReadset := by
  rfl

theorem unknown_workflow_never_acts_as_matching_current_workflow
    (impact : ImpactStanding) :
    decideAgent .unknown impact = .lookupOwner := by
  cases impact <;> rfl

#print axioms no_domain_reuse_without_closed_owner_readset
#print axioms no_domain_reuse_without_domain_owner_proof
#print axioms domain_reuse_requires_all_three
#print axioms matching_workflow_plus_changed_source_requests_domain_qualification
#print axioms matching_workflow_plus_unknown_impact_requests_readset_qualification
#print axioms unknown_workflow_never_acts_as_matching_current_workflow

end OrdivonJustification
