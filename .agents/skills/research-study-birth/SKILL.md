---
name: research-study-birth
description: "Route creation or adoption of a new Ordivon research study, paper project, empirical study, benchmark study, replication, systematic review, meta-science study, or preregistered study through the canonical Research-v2 Study Birth owner. Use before creating a new forward research directory or assembling a research data/tool stack. Do not copy Paper-1/Paper-3 layouts or reconstruct Arrow/Parquet/DuckDB/Polars/pandas choices from memory; the Research owner resolves the current versioned birth policy and data-plane profile."
compatibility: "Requires access to the current Ordivon Research-v2 source authority and its locked Python environment. This Skill routes to that owner; it does not own scientific methods, data-plane defaults, or execution authority."
metadata:
  source-authority: "Ordivon Research-v2 versioned Study Birth policy and provider"
---

# Research Study Birth

Use this Skill when the requested action is to **start, scaffold, adopt, or formalize a new forward Research Study**. It is a consumer route into the Research-v2 owner, not a second copy of the Research architecture.

## Owner boundary

The canonical Research-v2 source owns:

- the current Study Birth policy pointer;
- versioned frozen Birth Policies;
- versioned frozen data-plane profiles;
- method-authority bindings;
- the `ordivon-research-study` provider;
- Study-local `study-birth.json` bindings and admission checks.

This Skill MUST NOT duplicate the current provider list or infer defaults from an older paper. Read them from the Research owner at execution time.

Workstation may materialize the locked environment and Runtime may execute commands, but neither becomes Research Study semantic authority. Method/reporting standards remain external scientific authorities.

## Procedure

1. Resolve the **current** Research-v2 source authority. On the current local deployment this has historically been `/root/projects/ordivon-research-v2`; re-read current owner/source truth rather than treating that path or any remembered revision as immutable.
2. Before creating files, ask the Research owner for its live supported Study types and active defaults:

   ```bash
   uv run --frozen --extra data --extra dev --extra workflow \
     ordivon-research-study list-study-types

   uv run --frozen --extra data --extra dev --extra workflow \
     ordivon-research-study defaults
   ```

3. Classify the requested Study to one supported `study-type`. Scientific method selection remains governed by the Research method-authority bindings; do not invent a local substitute.
4. Create the Study through the provider, not by hand:

   ```bash
   uv run --frozen --extra data --extra dev --extra workflow \
     ordivon-research-study create \
     --study-id <stable-study-id> \
     --study-type <supported-study-type> \
     --title <title>
   ```

5. If an existing directory under the managed Study root must be brought under the system, use the provider's `adopt` path. Do not use adoption to bless a legacy Paper-1/Paper-3 layout or bypass the managed root.
6. Read the generated `study-birth.json`. Treat its exact policy/profile paths and SHA-256 bindings as the Study's birth contract.
7. If the workload genuinely needs a non-default provider, change the Study-local binding only with an explicit evidenced override. Never edit a frozen default profile in place merely to accommodate one Study.
8. Run the Research owner's `check-all` / repository verification before integration. A passing Runtime process or tool command is physical evidence, not scientific acceptance.

## Strong defaults, not hard lock-in

The purpose of Study Birth is to remove manual assembly while retaining substitution. A default may be replaced when a concrete workload needs another provider, but the deviation must be explicit, local to the Study, evidenced, and mechanically validated.

The following are therefore anti-patterns:

- creating `research/paper4`, `papers/paper4`, or another historical-layout sibling by hand;
- copying a previous Study's dependency list or data-plane choices;
- treating pandas, Polars, DuckDB, Arrow, Parquet, PostgreSQL, Snakemake, DVC, MLflow, or any other tool as scientific authority merely because it is selected;
- silently changing a provider without a Study-local override;
- editing an adopted frozen Birth Policy or data-plane profile in place;
- rewriting frozen Paper-1/Paper-3 scientific artifacts only to conform to the new forward layout.

## Relationship to Method Router

`method-router` chooses the smallest useful reasoning method for an already scoped problem. `research-study-birth` establishes the machine-owned **project birth/admission envelope** for a new Research Study. If both are relevant, Study Birth establishes the Study contract and the method authority binding; Method Router may then help choose additional analysis Skills without taking ownership of the Study lifecycle.

## Stop condition

Stop the birth phase when the Study exists under the managed Research root, its generated birth spec validates against the exact frozen policy/profile bindings, and the Research owner admission check passes. Continue scientific work only from that admitted Study state.
