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

end OrdivonJustification
