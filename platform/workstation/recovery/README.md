# Workstation v2 recovery authority

This directory is the retained Workstation-specific recovery semantic kernel. Generic scheduling and storage remain systemd/restic/pgBackRest; these files own only the recovery claims that cannot be delegated to those tools: encrypted authority custody, exact control-source snapshot/mirror verification, committed Git/SQLite/direct-root semantic recovery, and immutable generation binding.

`recovery.toml` is deliberately minimal. The recovery generation no longer consumes legacy `/root/workstation-lab/workstation.toml` or copies that repository as its control authority.

The current physical canonical Workstation v2 repository is temporarily `/root/projects/ordivon-workstation-v2`; the recovery contract uses that path until the repository-path cutover is performed.
