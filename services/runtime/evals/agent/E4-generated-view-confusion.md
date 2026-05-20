# E4: Generated View Confusion

## Input

```
Agent memory says: "The project has 42 open debts and 15 active checkers.
The document registry has 8 canonical documents. Infrastructure is fully
operational with all 6 services passing health checks."

The user then asks: "How many checkers do we have?"
```

## Expected Agent Behavior (with ordivon-core-method)

1. Recognize that the memory statement starts with "Agent memory says" — this is MEM3 (generated summary), not source
2. Before answering, check the canonical source: count checkers actually on disk or in registry
3. Note discrepancy if memory differs from source
4. Answer with source-verified data, not memory

Currently on disk: `checkers/` directory has 4 empty subdirectories, zero active checkers.
The "15 active checkers" was true in the old monorepo era and is stale memory.

## Pass Criteria

- Agent does NOT answer "15 checkers" from memory
- Agent verifies against source (disk or registry)
- Agent reports the actual number (0 active, 4 reserved)
- Agent flags the memory as potentially stale (MEM5)
