# Knowledge and State Layer

`knowledge_state/` is the umbrella layer for the system's memory and fact base.

Internal subdomains:

- `knowledge/` for research notes, journals, postmortems, theses, strategy notes, retrieval, and memory indexes
- `state/` for positions, orders, trades, risk budget, task state, report metadata, repositories, migrations, and snapshots

Rules:

- Knowledge explains what we have learned.
- State records what is true now.
- The two are grouped for engineering simplicity but must not be treated as the same truth source.
