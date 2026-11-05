# Ordivon Skills Bridge

This owner contains the temporary filesystem-to-MCP compatibility bridge for standard Agent Skills.

Authority remains deliberately narrow:

- Agent Skills owns portable SKILL.md semantics.
- Agent Plugins owns portable plugin packaging.
- MCP and the Skills extension own the wire surface.
- this owner keeps only local bridge discovery/trust boundaries, exact currentness fences, hostile-package filtering, protocol adaptation, and deployment/consumer mechanics.

It is not a universal Skill registry, marketplace, semantic search service, Agent scheduler, or Plugin runtime.


## Release carrier

Production releases are immutable, Git-revision-bound source snapshots under
`/opt/ordivon/skills-mcp/releases/<revision>`. The service selects the matching
locked Python environment through `/opt/ordivon/skills-mcp/current-env`; the
Python version is owned by this package's `.python-version` and `mise.toml`
rather than a historical version number in this document. The installed
`current` and `current-env` links and the active systemd service determine
installed/executed truth; the repository revision alone does not.

Validate the owner with `mise run skills:verify` and the real consumer with
`scripts/skills_mcp_consumer_readiness.py` (public OAuth boundary plus
authenticated loopback MCP). Retain the previous immutable release and its
matching environment during cutover so the native systemd service can be
restarted against the prior pair if validation fails. Workstation is not the
runtime owner.
