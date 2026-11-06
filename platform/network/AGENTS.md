# Network-specific Agent entrypoint

Follow the root monorepo AGENTS.md. For Network responsibilities and real
consumer evidence read [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md). Human
operator instructions are in [docs/HUMAN_GUIDE.md](docs/HUMAN_GUIDE.md).

Network is NOT a universal VPN controller. Generic core, one Gluetun Provider,
individual Consumer destination policies, Workstation bootstrap, Runtime Jobs
and Security credentials have different owners. Use task --list-all from
platform/network and the native current source/install/load/consumer evidence.

Source-only tests cannot prove a live application's VPN path. UNKNOWN is
never FALSE or PASS. Use existing GitHub PR/CI/merge queue. Clean storage
only through the original Podman/systemd/Runtime owner lifecycle after
consumer reachability is resolved, never by deleting active worktree roots.
