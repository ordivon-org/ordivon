import RecursiveLegoRefinement

/- Consumer-owned exact R2.1 retirement permission: the producer cannot
   weaken no_live_consumer_if_closed_and_current to True and silently pass
   the native Formal owner. All premises are explicit and independently
   declared here, no new LEGO field, registry or theorem calculus. -/
namespace OrdivonR21.NativeRetirementChallenge

theorem remove_only_if_all_consumer_closure_premises_hold
    {Node : Type}
    (workspace : Node)
    (snapshotEdges currentEdges : Node → Node → Prop)
    (snapshotLive currentLive observed : Node → Prop)
    (hEdges : ∀ upstream downstream,
      currentEdges upstream downstream → snapshotEdges upstream downstream)
    (hLive : ∀ node, currentLive node → snapshotLive node)
    (hComplete : ∀ node,
      OrdivonR21.ImpactReach snapshotEdges
        (fun candidate => candidate = workspace) node →
      snapshotLive node → observed node)
    (hNoWitness : ∀ node, ¬ observed node) :
    ¬ OrdivonR21.RetirementClosure.HasLiveConsumer
        currentEdges currentLive workspace := by
  exact OrdivonR21.RetirementClosure.no_live_consumer_if_closed_and_current
    workspace snapshotEdges currentEdges snapshotLive currentLive observed
    hEdges hLive hComplete hNoWitness

theorem empty_observer_without_coverage_cannot_permit_delete :
    ∃ observed : OrdivonR21.DisjointLEGO → Prop,
      (∀ node, ¬ observed node) ∧
      OrdivonR21.RetirementClosure.HasLiveConsumer OrdivonR21.aToB
        (fun node => node = .b) .a :=
  OrdivonR21.RetirementClosure.no_match_without_coverage_is_not_safe

theorem new_edge_defeats_historical_no_consumer_witness :
    (¬ OrdivonR21.RetirementClosure.HasLiveConsumer OrdivonR21.noDependency
      (fun node : OrdivonR21.DisjointLEGO => node = .b) .a) ∧
    OrdivonR21.RetirementClosure.HasLiveConsumer OrdivonR21.aToB
      (fun node => node = .b) .a :=
  OrdivonR21.RetirementClosure.new_edge_invalidates_old_negative_observation

theorem newly_live_consumer_defeats_old_negative_witness :
    (¬ OrdivonR21.RetirementClosure.HasLiveConsumer OrdivonR21.aToB
      (fun _ : OrdivonR21.DisjointLEGO => False) .a) ∧
    OrdivonR21.RetirementClosure.HasLiveConsumer OrdivonR21.aToB
      (fun node => node = .b) .a :=
  OrdivonR21.RetirementClosure.new_live_consumer_invalidates_old_negative_observation

#print axioms OrdivonR21.NativeRetirementChallenge.remove_only_if_all_consumer_closure_premises_hold
#print axioms OrdivonR21.NativeRetirementChallenge.empty_observer_without_coverage_cannot_permit_delete
#print axioms OrdivonR21.NativeRetirementChallenge.new_edge_defeats_historical_no_consumer_witness
#print axioms OrdivonR21.NativeRetirementChallenge.newly_live_consumer_defeats_old_negative_witness
end OrdivonR21.NativeRetirementChallenge
