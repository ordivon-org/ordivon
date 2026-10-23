# Harness Queue Portability R1

Date: 2026-09-22
Status: REMOTE PROVEN

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

## Remote evidence

- Harness portability PR #21 head b2aa6e10e545eb6a75f944490f7e4704950195f6:
  pull-request run 35725482208 passed.
- Merge Queue synthesized ceba591066c98999e404bdfe5f72a66ef3ed76ea:
  merge-group run 35725780805 passed and became main.
- The previously failing real Experimental Episode producer PR #20 was refreshed
  onto that protected main. Pull-request run 35726259787 passed.
- Merge Queue then synthesized 06b932777ee03b421e45f021f51efebd0053a089:
  merge-group run 35726560495 passed and merged.
- Final main push run 35726848574 passed on that exact synthetic revision.

Therefore the split is proven on both a Harness-owner change and the real
cross-owner producer that originally exposed the clean-runner failure.
