# Private Registry -> Agent Skills migration

Date: 2026-09-13

## Decision

Retire the Ordivon-private `registry/artifact/*.json` discovery/identification experiment and adopt the Agent Skills open format for procedural knowledge discovery and progressive disclosure.

## Replacement

- project discovery path: `.agents/skills/`
- skill: `.agents/skills/artifact-work/SKILL.md`
- detailed artifact family knowledge: `.agents/skills/artifact-work/references/*.md`
- executable provider/tool discovery: current harness / MCP / CLI / API / application environment
- source implementation authority: `/root/projects/ordivon/capabilities/artifact`

## Why

The private registry duplicated a problem now covered by a cross-client convention: skill metadata discovery (`name`, `description`), model-driven activation, progressive disclosure, linked references and optional scripts/assets.

The old JSON also mixed two different concerns. Agent Skills owns procedural knowledge discovery; MCP/harness/environment discovery owns executable tools. The new split preserves that boundary.

## Non-migration

No custom resolver, vector index, trigger matcher, registry daemon, skill database or Ordivon-specific Skill schema is introduced. Add such machinery only if measured scale/retrieval problems later require it.
