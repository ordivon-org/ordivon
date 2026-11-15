-- Generic abstract proof for Host's native PostgreSQL Unicode GIN search.
-- Character sequences are finite lists: no assumption about Chinese word
-- segmentation, collation, bytes, database transactions, or stored rows.
-- The SQL function, index operator, and installed MCP are separate
-- implementation-refinement and real-consumer obligations.

universe u

namespace OrdivonHostUnicodeGram

-- Constructive append-associativity proof: do not inherit the standard
-- library theorem's propext dependency for this small Host theorem.
theorem append_assoc_constructive {α : Type u}
    (xs ys zs : List α) :
    (xs ++ ys) ++ zs = xs ++ (ys ++ zs) := by
  induction xs with
  | nil => rfl
  | cons x tail ih =>
    change x :: ((tail ++ ys) ++ zs) = x :: (tail ++ (ys ++ zs))
    exact congrArg (List.cons x) ih

-- Group the five source segments using only structurally proved equalities.
-- Explicit parentheses match Lean's left-associative list append.
theorem append_five_constructive {α : Type u}
    (a b c d e : List α) :
    (a ++ ((b ++ c) ++ d)) ++ e =
    ((a ++ b) ++ c) ++ (d ++ e) := by
  calc
    (a ++ ((b ++ c) ++ d)) ++ e
        = ((a ++ (b ++ c)) ++ d) ++ e :=
          congrArg (fun xs : List α => xs ++ e)
            (append_assoc_constructive a (b ++ c) d).symm
    _ = (((a ++ b) ++ c) ++ d) ++ e :=
          congrArg (fun xs : List α => (xs ++ d) ++ e)
            (append_assoc_constructive a b c).symm
    _ = ((a ++ b) ++ c) ++ (d ++ e) :=
          append_assoc_constructive ((a ++ b) ++ c) d e

def IsSubstring {α : Type u} (needle text : List α) : Prop :=
  ∃ left right, text = left ++ needle ++ right

def IsGram3 {α : Type u} (gram text : List α) : Prop :=
  gram.length = 3 ∧ IsSubstring gram text

-- Model PostgreSQL GIN array containment over distinct 3-codepoint windows.
-- Multiplicity is irrelevant: a true substring's every window must occur.
def HasCandidateGrams {α : Type u} (query body : List α) : Prop :=
  ∀ gram, IsGram3 gram query → IsGram3 gram body

theorem substring_transitive {α : Type u}
    {needle middle body : List α}
    (inner : IsSubstring needle middle)
    (outer : IsSubstring middle body) :
    IsSubstring needle body := by
  rcases inner with ⟨beforeNeedle, afterNeedle, hInner⟩
  rcases outer with ⟨beforeMiddle, afterMiddle, hOuter⟩
  refine ⟨beforeMiddle ++ beforeNeedle, afterNeedle ++ afterMiddle, ?_⟩
  calc
    body = beforeMiddle ++ middle ++ afterMiddle := hOuter
    _ = beforeMiddle ++ (beforeNeedle ++ needle ++ afterNeedle) ++ afterMiddle :=
      congrArg (fun x : List α => beforeMiddle ++ x ++ afterMiddle) hInner
    _ = (beforeMiddle ++ beforeNeedle) ++ needle ++ (afterNeedle ++ afterMiddle) :=
      append_five_constructive beforeMiddle beforeNeedle needle afterNeedle afterMiddle

-- General theorem: no exact match can be filtered out by GIN 3-gram candidates.
theorem exact_implies_candidate {α : Type u} {query body : List α}
    (exact : IsSubstring query body) :
    HasCandidateGrams query body := by
  intro gram hGram
  exact ⟨hGram.1, substring_transitive hGram.2 exact⟩

-- Candidate-only contains false positives. Host MUST retain exact strpos.
theorem candidate_and_exact_iff_exact {α : Type u} {query body : List α} :
    (HasCandidateGrams query body ∧ IsSubstring query body) ↔
    IsSubstring query body := by
  constructor
  · exact And.right
  · intro exact
    exact ⟨exact_implies_candidate exact, exact⟩

#print axioms append_five_constructive
#print axioms substring_transitive
#print axioms exact_implies_candidate
#print axioms candidate_and_exact_iff_exact

end OrdivonHostUnicodeGram
