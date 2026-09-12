# Workstation v2 retirement migration record

- Source: `/root/projects/ordivon-workstation-v2`
- Observed revision: `88c05d922d43`
- Retired: 2026-09-12
- New-model disposition: historical evidence only

Transferred responsibilities recorded by the source repository:

- Nix/Home Manager declarations -> Operations workstation declarations;
- WinGet/DSC declarations -> Operations Windows declarations;
- Netdata realization -> Operations observability/Ansible;
- osquery generic inventory -> Operations inventory queries;
- generic configuration consequence checks -> Operations tests.

No active Workstation-v2 capability is imported into Ordivon Next. Git history remains provenance.
