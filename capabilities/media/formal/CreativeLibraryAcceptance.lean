-- Abstract current-Catalog acceptance identity on already-parsed opaque tokens.
-- This MODEL is not Python implementation, hash collision or provider proof.
namespace OrdivonMedia

inductive CatalogRelation where
  | noSelectedCatalog
  | unboundAcceptance
  | differentCatalog
  | unboundFile
  | currentBinding
  deriving DecidableEq, Repr

def catalogRelation (selected accepted selectedFile acceptedFile : Option Nat) :
    CatalogRelation :=
  match selected, accepted with
  | none, _ => .noSelectedCatalog
  | some _, none => .unboundAcceptance
  | some s, some a =>
      if s = a then
        match selectedFile, acceptedFile with
        | some sf, some af =>
            if sf = af then .currentBinding else .differentCatalog
        | _, _ => .unboundFile
      else .differentCatalog

-- A current acceptance requires BOTH known, equal semantic and file identities.
theorem current_requires_both_identities (s a sf af : Option Nat) :
    catalogRelation s a sf af = .currentBinding <->
    Exists (fun semantic => Exists (fun file =>
      s = some semantic /\ a = some semantic /\
      sf = some file /\ af = some file)) := by
  cases s with
  | none => simp [catalogRelation]
  | some sv =>
    cases a with
    | none => simp [catalogRelation]
    | some av =>
      by_cases hs : sv = av
      case pos =>
        subst av
        cases sf with
        | none => simp [catalogRelation]
        | some fv =>
          cases af with
          | none => simp [catalogRelation]
          | some afv =>
            by_cases hf : fv = afv
            case pos =>
              subst afv
              simp [catalogRelation]
            case neg =>
              simp [catalogRelation, hf, eq_comm]
      case neg =>
        cases sf <;> cases af <;> simp [catalogRelation, hs, eq_comm]

theorem semantic_mismatch_is_historical (s a : Nat) (h : Not (s = a))
    (sf af : Option Nat) :
    catalogRelation (some s) (some a) sf af = .differentCatalog := by
  simp [catalogRelation, h]

theorem missing_catalog_is_unknown (a sf af : Option Nat) :
    catalogRelation none a sf af = .noSelectedCatalog := by
  rfl

theorem missing_file_cannot_be_current (s a sf : Option Nat) :
    Not (catalogRelation s a sf none = .currentBinding) := by
  intro h
  have hboth := (current_requires_both_identities s a sf none).mp h
  cases hboth with
  | intro semantic hex =>
    cases hex with
    | intro file hrest =>
      have impossible : (none : Option Nat) = some file := hrest.2.2.2
      cases impossible

theorem equal_known_identities_are_current (s f : Nat) :
    catalogRelation (some s) (some s) (some f) (some f) =
      .currentBinding := by
  simp [catalogRelation]

end OrdivonMedia
