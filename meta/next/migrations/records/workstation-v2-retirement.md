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

## Final archive closeout — 2026-09-14

Final archive commit: `74c068ac7bd2b3bee31a385f417c49ebd11cfba8`. A fresh bounded census again found no installed service/runtime binding to the Workstation-v2 repository; surviving current references are retirement/migration documentation. The historical-evidence-only disposition is unchanged.
