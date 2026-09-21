# Ordivon Skills Bridge

This owner contains the temporary filesystem-to-MCP compatibility bridge for standard Agent Skills.

Authority remains deliberately narrow:

- Agent Skills owns portable SKILL.md semantics.
- Agent Plugins owns portable plugin packaging.
- MCP and the Skills extension own the wire surface.
- this owner keeps only local bridge discovery/trust boundaries, exact currentness fences, hostile-package filtering, protocol adaptation, and deployment/consumer mechanics.

It is not a universal Skill registry, marketplace, semantic search service, Agent scheduler, or Plugin runtime.
