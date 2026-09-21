# C03 Skill Bridge Consumer Census R1

Date: 2026-09-21

Status: **per-consumer retirement complete; one exact compatibility consumer retained**

## Decision

The Skill MCP bridge is not a canonical Skill platform and must not be used by local clients that already consume Agent Skills natively. The current machine has exactly one evidence-backed reason to keep the bridge public: **ChatGPT cannot directly consume the same local Ordivon/vendor Agent Skill catalog exposed by the bridge**.

Therefore C03 does **not** globally delete `ordivon-skills-mcp.service`. It narrows the supported compatibility boundary to ChatGPT and records all other observed local consumers as bridge-free.

## Consumer census

| Consumer | Native mechanism | Skill MCP required? | Evidence |
|---|---|---:|---|
| ChatGPT custom app | Product-native skills plus custom MCP app | **Yes, retained** | Current ChatGPT session has `mcp__ordivon_skill__*`; native `skills__*` catalog does not include the local Ordivon/vendor catalog; bridge `resolve → read` succeeded for `obra-superpowers/test-driven-development`. |
| Codex local | `/root/.codex/skills` | No | Native root exists/populated; no active Codex config references the public bridge. |
| Hermes local | `/root/.hermes/skills` | No | Native root exists/populated; no active Hermes config references the public bridge. |
| Ordivon project/local harness | `/root/.agents/skills` | No | Standard local root exists/populated; no active local harness dependency on the public bridge was found. |

## Source versus consumer

The live bridge still lists `codex-user`, `hermes-user` and vendor trees in `compatibilitySources` / `additionalSources`. These are **input catalogs projected to the remote ChatGPT consumer**. They are not proof that Codex or Hermes consume Skill MCP.

This distinction prevents a false retirement decision:

```text
Codex/Hermes/native roots ── source bytes ──┐
vendor Agent Skills ───────────────────────┤
                                           ↓
                               temporary Skill MCP bridge
                                           ↓
                                  ChatGPT compatibility
```

Local Codex/Hermes execution remains:

```text
Agent Skills root → native client
```

and must not be routed through Skill MCP.

## Retained bridge boundary

The retained bridge may continue to provide only:

- `skills.list`
- `skills.search`
- `skills.resolve`
- `skills.read`

It must remain a bounded filesystem-to-network projection with digest/currentness/trust fences. It must not grow a marketplace, semantic owner, learned router, scheduler or private Skill ontology.

The current public OAuth application is intentionally ChatGPT-specific: DCR callback admission is scoped to `https://chatgpt.com/connector/oauth/*`.

## Exit condition

Global bridge retirement becomes admissible only when ChatGPT can consume the same local Agent Skills / Agent Plugin package directly with equivalent evidence for:

1. discovery;
2. exact activation/read;
3. refresh after Skill/package change;
4. project/user trust and permission boundaries;
5. no remaining local-filesystem-to-remote projection requirement.

Until then, deleting the bridge would remove real capability from the current ChatGPT consumer and would violate the consumer-evidence retirement rule.
