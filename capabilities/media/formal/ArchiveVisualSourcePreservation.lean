-- Source-to-visual relation conservation for an admitted Archive graph.
-- MODEL ONLY: Nat represents already-parsed opaque Work identity. This is not
-- proof of Python JSON parsing, hashing, SVG layout or user visual perception.
namespace OrdivonMedia

inductive ArchiveRelationKind where
  | derivative
  | consumer
  deriving DecidableEq, Repr

structure ArchiveEdge where
  fromId : Nat
  toId : Nat
  kind : ArchiveRelationKind
  deriving DecidableEq, Repr

-- All represented relations must belong to the source's typed relation set.
-- A type outside this two-element vocabulary must be rejected by the parser.
def knownEndpoints (workIds : List Nat) (relation : ArchiveEdge) : Prop :=
  relation.fromId ∈ workIds ∧ relation.toId ∈ workIds

def validArchive (workIds : List Nat) (sourceEdges : List ArchiveEdge) : Prop :=
  workIds.Nodup ∧ ∀ relation ∈ sourceEdges, knownEndpoints workIds relation

-- The actual renderer may choose any geometry, but not invent or drop factual
-- edges. Partial admission is explicit rather than silently filtering edges.
noncomputable def admitArchiveEdges (workIds : List Nat) (sourceEdges : List ArchiveEdge) :
    Option (List ArchiveEdge) := by
  classical
  exact if validArchive workIds sourceEdges then some sourceEdges else none

theorem admitted_edges_exact
    (workIds : List Nat) (sourceEdges rendered : List ArchiveEdge)
    (h : admitArchiveEdges workIds sourceEdges = some rendered) :
    rendered = sourceEdges := by
  by_cases good : validArchive workIds sourceEdges
  · simp [admitArchiveEdges, good] at h
    exact h.symm
  · simp [admitArchiveEdges, good] at h

theorem admitted_edge_count_exact
    (workIds : List Nat) (sourceEdges rendered : List ArchiveEdge)
    (h : admitArchiveEdges workIds sourceEdges = some rendered) :
    rendered.length = sourceEdges.length := by
  rw [admitted_edges_exact workIds sourceEdges rendered h]

theorem invalid_archive_rejects
    (workIds : List Nat) (sourceEdges : List ArchiveEdge)
    (invalid : ¬ validArchive workIds sourceEdges) :
    admitArchiveEdges workIds sourceEdges = none := by
  simp [admitArchiveEdges, invalid]

theorem admitted_relations_have_known_endpoints
    (workIds : List Nat) (sourceEdges rendered : List ArchiveEdge)
    (h : admitArchiveEdges workIds sourceEdges = some rendered)
    (r : ArchiveEdge) (included : r ∈ rendered) :
    knownEndpoints workIds r := by
  have equal := admitted_edges_exact workIds sourceEdges rendered h
  subst rendered
  have good : validArchive workIds sourceEdges := by
    by_cases valid : validArchive workIds sourceEdges
    · exact valid
    · have rejected := invalid_archive_rejects workIds sourceEdges valid
      rw [rejected] at h
      cases h
  exact good.2 r included

-- Nonvacuity + independent negative controls, not an assumed universal PASS.
private def supportedEdge : ArchiveEdge :=
  {fromId := 1, toId := 2, kind := .derivative}

example : admitArchiveEdges [1, 2] [supportedEdge] = some [supportedEdge] := by
  simp [admitArchiveEdges, validArchive, knownEndpoints, supportedEdge]
example : admitArchiveEdges [1] [supportedEdge] = none := by
  simp [admitArchiveEdges, validArchive, knownEndpoints, supportedEdge]
example : admitArchiveEdges [1, 1, 2] [supportedEdge] = none := by
  simp [admitArchiveEdges, validArchive, knownEndpoints, supportedEdge]

end OrdivonMedia
