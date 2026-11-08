-- Ordivon Media: bounded three-valued dependency-impact model.
-- File-system and process observations are *not* proved by these theorems.
-- Source declarations, operational identity and cache authorization remain distinct.
namespace OrdivonMedia

inductive ByteStanding where
  | matches
  | drift
  | unknown
  deriving DecidableEq, Repr

inductive ImpactStanding where
  | noDrift
  | revalidate
  | unknown
  deriving DecidableEq, Repr

def byteImpact : ByteStanding → ImpactStanding
  | .matches => .noDrift
  | .drift => .revalidate
  | .unknown => .unknown

def joinImpact : ImpactStanding → ImpactStanding → ImpactStanding
  | .revalidate, _ => .revalidate
  | _, .revalidate => .revalidate
  | .unknown, _ => .unknown
  | _, .unknown => .unknown
  | .noDrift, .noDrift => .noDrift

def dependentImpact (self : ByteStanding) (dependencies : List ImpactStanding) :
    ImpactStanding :=
  dependencies.foldl joinImpact (byteImpact self)

theorem source_changed_is_revalidation :
    dependentImpact .drift [] = .revalidate := by
  rfl

theorem source_missing_is_unknown :
    dependentImpact .unknown [] = .unknown := by
  rfl

theorem exact_observed_bytes_no_local_drift :
    dependentImpact .matches [] = .noDrift := by
  rfl

theorem changed_predecessor_affects_clean_successor :
    dependentImpact .matches [.revalidate] = .revalidate := by
  rfl

theorem unknown_predecessor_cannot_prove_unchanged :
    dependentImpact .matches [.unknown] = .unknown := by
  rfl

theorem independent_clean_branch_not_invalidated :
    dependentImpact .matches [.noDrift] = .noDrift := by
  rfl

theorem known_drift_dominates_unknown :
    dependentImpact .drift [.unknown] = .revalidate := by
  rfl

-- The concrete branching shape follows the owner-declared sonic topology;
-- equality here does not qualify the historical SoX/FFmpeg invocation.
def sonicSource (input : ByteStanding) : ImpactStanding :=
  dependentImpact input []

def sonicMaster (input : ByteStanding) : ImpactStanding :=
  dependentImpact input [sonicSource .matches]

def sonicDelivery (master : ImpactStanding) : ImpactStanding :=
  dependentImpact .matches [master]

theorem source_drift_reaches_all_downstream :
    sonicDelivery (dependentImpact .matches [sonicSource .drift]) = .revalidate := by
  rfl

theorem isolated_delivery_drift_does_not_change_master :
    sonicMaster .matches = .noDrift ∧
    dependentImpact .drift [sonicMaster .matches] = .revalidate := by
  constructor <;> rfl

-- No theorem grants cache reuse or provider/publication authority.
end OrdivonMedia
