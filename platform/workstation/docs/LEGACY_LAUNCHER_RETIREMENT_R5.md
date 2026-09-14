# Legacy Workstation launcher retirement — R5

Date: 2026-09-14

A tracked-source census found zero current external consumers of `/root/tools/bin/workstation-semantic`; its live catalog exposes only `workstation.equipment.resolve`, whose currently used browser/managed/professional binding paths are supplied by the Workstation v2 `equipment-binding` surface. The legacy semantic catalog's unused `isolated` schema has no tracked production consumer and is not a reason to preserve a second binding authority.

`/root/tools/bin/engineering-python` is referenced only by historical design experiments inside legacy Workstation. Current Laboratory/domain owners do not reference the stable path.

Both launchers are therefore removed from the live node by Workstation v2 Ansible. Historical implementation remains recoverable from legacy Git. This removal does not delete domain evidence or the immutable Agent Automation release.
