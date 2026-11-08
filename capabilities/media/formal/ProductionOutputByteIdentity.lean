-- Media output byte comparison: abstract model over *already selected* bytes.
-- Opaque Nat tokens stand for exact digest identities, not hashing/file I/O.
-- No implication about editorial approval, current source truth or publication.
namespace OrdivonMedia

inductive OutputByteRelation where
  | unknown
  | matches
  | differs
  deriving DecidableEq, Repr

def outputByteRelation (declared observed : Option Nat) : OutputByteRelation :=
  match declared, observed with
  | some expected, some actual =>
      if expected = actual then .matches else .differs
  | _, _ => .unknown

theorem absent_declared_is_unknown (observed : Option Nat) :
    outputByteRelation none observed = .unknown := by
  cases observed <;> rfl

theorem absent_observation_is_unknown (declared : Option Nat) :
    outputByteRelation declared none = .unknown := by
  cases declared <;> rfl

theorem equal_known_digest_matches (digest : Nat) :
    outputByteRelation (some digest) (some digest) = .matches := by
  simp [outputByteRelation]

theorem different_known_digest_differs (declared observed : Nat)
    (different : declared ≠ observed) :
    outputByteRelation (some declared) (some observed) = .differs := by
  simp [outputByteRelation, different]

theorem matches_requires_known_equal (declared observed : Option Nat) :
    outputByteRelation declared observed = .matches →
    ∃ digest, declared = some digest ∧ observed = some digest := by
  cases declared with
  | none => simp [outputByteRelation]
  | some d =>
    cases observed with
    | none => simp [outputByteRelation]
    | some o =>
      by_cases h : d = o
      · subst o
        simp [outputByteRelation]
      · simp [outputByteRelation, h]

-- Output lifecycle state is independently source-declared; byte evidence must
-- never change its editorial/production standing.
def preserveOutputStatus (declaredStatus : Nat) (_ : OutputByteRelation) : Nat :=
  declaredStatus

theorem byte_evidence_never_promotes_status (status : Nat) (relation : OutputByteRelation) :
    preserveOutputStatus status relation = status := by
  rfl

end OrdivonMedia
