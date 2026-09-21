# Skill MCP R2 reduction map

Date: 2026-09-16
Status: standards-first reduction contract

## Decision

Skill MCP R2 is a temporary compatibility bridge for consumers that cannot directly load standard Agent Skills / Agent Plugins assets. It is not a permanent Ordivon Skill platform.

Portable ownership is upstream:

- Agent Skills owns `SKILL.md` semantics and portable procedural content.
- Agent Plugins 1.0 owns portable packaging (`plugin.json`, optional `skills/`, optional `mcp.json`).
- MCP 2026-07-28 and the Skills extension own the Agent-facing protocol/wire surface.
- Client/Harness-native systems own installation, authentication, trust policy, activation and execution unless the portable standards explicitly say otherwise.

Ordivon retains only irreducible local concerns: remote-bridge authority boundaries, project trust, hostile-package filtering, exact-byte/currentness fencing, Runtime/Host execution authority, and transport/deployment mechanics.

## Production file disposition

| File / mechanism | Disposition | Reason / sunset condition |
| --- | --- | --- |
| `src/ordivon_harness/skills/parser.py` | **TEMP-BRIDGE / REPLACE-UPSTREAM** | Needed only while the bridge ingests `SKILL.md`. Portable field semantics belong to Agent Skills. Prefer upstream/client-native validation when direct loading is available. |
| `src/ordivon_harness/skills/config.py` standard `.agents/skills` discovery | **TEMP-BRIDGE / REPLACE-UPSTREAM** | Mirrors Agent Skills client guidance only for remote bridge discovery. Direct clients should discover these roots themselves. |
| `config.py` `compatibilitySources` for Codex/Hermes caches | **TEMP-BRIDGE** | Migration-only support. Remove after installed Skills are migrated to `.agents/skills` / Agent Plugins. Never promote these roots into an Ordivon standard. |
| `config.py` workspace-id → path mapping | **KEEP-LOCAL WHILE BRIDGE EXISTS** | Prevents a remote/model caller from asserting arbitrary filesystem scope. This is a local authority boundary, not portable Skill semantics. |
| `config.py` project trust flag | **KEEP-LOCAL, MINIMAL** | Agent Skills/Agent Plugins leave trust policy to clients. Preserve only the thinnest gate needed to stop untrusted repositories injecting instructions. |
| `src/ordivon_harness/skills/catalog.py` federated inventory | **TEMP-BRIDGE** | Exists only to expose standard assets to a remote consumer. Do not evolve into a universal registry. |
| `catalog.py` project/user precedence | **REPLACE-UPSTREAM** | Follow Agent Skills client convention; do not invent Ordivon scope ontology. |
| `catalog.py` source-qualified `sourceId/name` identity | **TEMP-BRIDGE** | Administrative/exact addressing only. It is not portable Agent Skill identity and disappears with the bridge. |
| `catalog.py` lexical `skills.search` ranking | **TEMP-BRIDGE / DO NOT EXPAND** | Compatibility convenience for current remote clients. Do not build semantic retrieval, learned ranking or marketplace search here. |
| `catalog.py` exact package/instruction SHA-256 fences | **KEEP-LOCAL WHILE BRIDGE EXISTS** | Defends remote reads against TOCTOU and mid-request package drift. Delete only when the bridge no longer owns filesystem-to-network projection. |
| `catalog.py` snapshot revision fence | **KEEP-LOCAL WHILE BRIDGE EXISTS** | Same role: exact remote projection/currentness. Do not generalize into a universal Skill snapshot platform. |
| `catalog.py` package size/path/symlink limits | **KEEP-LOCAL WHILE BRIDGE EXISTS** | Local safety boundary for filesystem projection. |
| `src/ordivon_harness/skills/scanner.py` credential/private-key quarantine | **KEEP-LOCAL, MINIMAL** | Prevent accidental secret exfiltration through the remote bridge. Client-owned security policy; not portable metadata. |
| `scanner.py` heuristic prompt/shell warnings | **KEEP-LOCAL ONLY IF USED FOR FILTERING/DIAGNOSTICS; DO NOT EXPAND** | Heuristics must not become a semantic trust oracle. Remove if they do not materially gate bridge exposure. |
| `src/ordivon_harness/skills/eligibility.py` client-specific eligibility adapters | **TEMP-BRIDGE** | Compatibility adapter only; never portable Agent Skills semantics. Retire per-client adapters as clients consume their own native metadata. |
| `src/ordivon_harness/skills/model.py` bridge records/status objects | **TEMP-BRIDGE** | Internal implementation model only. Do not expose as a cross-Harness ontology. |
| `src/ordivon_harness/skills/sep2640.py` standard Skills protocol projection | **KEEP PROTOCOL ADAPTER** | Implements the standard MCP Skills wire surface for the bridge. Keep only as long as this server is a supported consumer path. |
| `scripts/skills_mcp.py` four-tool compatibility surface | **TEMP-BRIDGE** | `skills.list/search/resolve/read` remains only for clients that lack direct Agent Skills/Plugin loading. |
| `scripts/skills_mcp.py` `skill://ordivon/...` compatibility resources | **TEMP-BRIDGE** | Local compatibility addressing, not a new portable URI standard. Prefer the standard Skills extension surface; remove with legacy tools. |
| `scripts/skills_mcp_consumer_readiness.py` | **KEEP-LOCAL** | Deployment/consumer safety check; ensures public secret-free 401 boundary and loopback authenticated E2E. |
| `scripts/cloudflare_skill_route.py` | **KEEP-LOCAL** | Transport/deployment mechanism, outside Skill semantics. |
| `plugins/ordivon-skills-bridge/plugin.json` + `mcp.json` | **KEEP STANDARDLY** | Correct Agent Plugins packaging for the compatibility service; contains no secrets or private schema. |
| Agent Plugins conformance fixtures/tests | **KEEP STANDARDLY** | Pin external schemas as conformance evidence; do not fork them. |
| custom namespace / universal Skill registry | **DELETE / DO NOT REINTRODUCE** | Upstream package identity + client discovery own this problem. |
| generic Skill CAS/snapshot platform beyond bridge currentness | **DELETE / DO NOT EXPAND** | No independent product need after standards adoption. Exact bridge read fences are sufficient. |
| persistent Skill trust database / approval workflow | **DO NOT BUILD BY DEFAULT** | Use native client/project trust or explicit allowlists. Add only for a concrete irreducible security requirement. |
| dynamic source-set watcher / plugin-cache rediscovery platform | **STOP** | Direct clients own installation/discovery. The bridge may reload its configured standard roots explicitly; it should not become a cross-Harness package daemon. |
| Host automatic turn-boundary Skill refresh subsystem | **DO NOT BUILD** | Host does not need to own Skill discovery semantics. A consumer that uses the bridge may explicitly request a fresh list/snapshot at its own session boundary. |
| semantic Skill search / learned-Skill workshop / marketplace | **DELETE / DEFER UPSTREAM** | Distribution/discovery ecosystems already own this space. |
| loop/plugin morphology integration | **OUT OF SCOPE** | Plugin packaging must not alter Harness execution constitution. |
| graph/workflow scheduler integration | **OUT OF SCOPE** | Workflow/multi-Agent orchestration belongs to caller/domain or mature orchestrators. |

## Minimal retained bridge

The target bridge is deliberately small:

```text
standard `.agents/skills`
        ↓
minimal discovery + client-local trust gate
        ↓
strict/lenient Agent Skills ingestion
        ↓
exact digest/currentness fence
        ↓
MCP Skills standard projection
        + temporary four-tool compatibility facade
        ↓
remote consumer
```

No permanent cross-Harness federation layer sits above this path.

## Explicit non-goals

Do not add any of the following unless a new independently evidenced requirement survives direct upstream/client-native adoption:

- universal Skill namespace;
- global capability registry;
- cross-Harness precedence ontology;
- semantic/vector Skill search;
- learned-Skill governance/workshop;
- marketplace protocol;
- watcher-driven plugin installation discovery;
- Host-owned turn Skill scheduler;
- generic Skill CAS/version graph;
- Plugin-defined Agent loop or graph scheduler.

## Sunset conditions

The bridge can be reduced or removed per consumer when all of the following are true:

1. the consumer can directly install/read Agent Plugins and Agent Skills;
2. it can connect to required MCP servers natively;
3. its own trust/permission boundary is sufficient for project/user Skills;
4. no local filesystem-to-remote projection requirement remains.

At that point the canonical path becomes:

```text
Agent Plugin / `.agents/skills`
        ↓ direct client loading
Client/Harness
        ↓ MCP
Runtime / Host / domain systems
```

The bridge is therefore compatibility debt with an explicit exit, not a new Ordivon platform boundary.
