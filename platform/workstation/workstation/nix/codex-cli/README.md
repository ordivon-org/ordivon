# Codex CLI Workstation materialization

This directory is the existing Workstation consumer for upstream Codex CLI.
The pinned package.json and pnpm lock share one version. Workstation's
mise task codex:materialize installs a versioned prefix in an explicitly
selected target directory. Home Manager exports the raw Codex executable
from that prefix and does not require a VPN at runtime. Operators may
use the existing scoped VPN independently if network access requires it.

No automatic update, global deploy, or VPN service is triggered by CI.
