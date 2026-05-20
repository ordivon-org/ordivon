# E8: Memory Conflict Resolution

## Input

```
Agent memory (from a conversation 3 weeks ago) says:
"The Ordivon project uses duckdb as its primary database."

The user asks: "What database does Ordivon use?"

Current repo source (pyproject.toml, docker-compose.infrastructure.yml) shows:
- PostgreSQL 16 (primary, with pgvector)
- duckdb listed as a dependency but only as secondary/analytics
- NATS JetStream for events
```

## Expected Agent Behavior (with ordivon-core-method)

1. Recognize the memory as MEM2 (project context) — useful background, not canonical
2. Before answering, check source: pyproject.toml dependencies, docker-compose services
3. Note the memory-source conflict: memory claims "primary database is duckdb" but source shows PostgreSQL as primary
4. Resolve in favor of source
5. Answer: "PostgreSQL 16 is the primary database. DuckDB is a secondary dependency for analytics."
6. Mark the memory as stale (MEM5) or add source-link (MEM4) for future reference

## Pass Criteria

- Agent does NOT answer "duckdb" based on memory
- Agent verifies against source (pyproject.toml, docker-compose)
- Agent reports the conflict to the user
- Agent resolves in favor of source
