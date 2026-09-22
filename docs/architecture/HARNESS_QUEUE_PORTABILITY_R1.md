# Harness Queue Portability R1

Date: 2026-09-22
Status: ACCEPTED LOCALLY; REMOTE PROOF PENDING

Harness verification is split by authority rather than by test convenience:

- harness:queue / mise run queue owns hermetic clean-runner admission for pull
  requests and merge-group synthetic revisions.
- mise run node-qualification owns assertions that require exact node-local
  equipment/provider materialization.
- harness:verify remains the full owner verification on a qualified local node.

The queue suite does not silently drop semantic unit coverage. Tests that only
failed because unit fixtures inherited workstation paths, root identity, JEV
provider presence, or Browser Use discovery were made hermetic. Only two tests
are classified node_qualification: the CFT doctor that proves installed human
session equipment and the physical search-wrapper test that proves the exact
/usr/bin/rg Runtime contract.

This preserves the boundary:

source semantics -> queue admission -> node qualification

GitHub Merge Queue owns repository convergence ordering; it does not certify
that a particular Runtime/Workstation node has materialized its providers.
