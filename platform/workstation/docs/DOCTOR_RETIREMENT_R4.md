# Legacy Workstation Doctor retirement — R4

Date: 2026-09-14

A tracked-source + live-systemd census found no current external production consumer of `/root/workstation-lab/scripts/agent_workstation_doctor.py` or `task agent:doctor`. The only executable references are self-references inside the legacy Workstation repository and its tests.

Workstation v2 therefore does **not** port the giant Doctor. Its generic observation responsibilities are already supplied by the selected mature substrates (osquery/pacman/WinGet, Prometheus/node_exporter, Gatus, journald/Vector/Loki, systemd, Ansible/DSC/Nix). Stronger retained claims have independent narrow verifiers: exact tool bindings, Windows Runtime provider status, and immutable recovery-generation verification. Runtime, Network, Host, Security and domain E2Es retain their own truth.

Retirement means the legacy Doctor is historical/compatibility source only; it is not a Workstation v2 readiness gate and must not be consulted to infer a universal node green/red standing.
