# External Authority Catalog R1

The catalog is a lightweight discovery substrate for external standards, professional guidance, venue/publisher rules and provider authority sources.

It does **not** decide whether an authority applies to a task. Applicability remains in task-local Standard-Native profiles.

## Design

The catalog follows the same separation repeatedly observed in mature registries/loaders:

```text
REGISTER -> DISCOVER -> SELECT -> LOAD -> BIND -> USE -> VERIFY
```

Do not collapse these stages.

### Source of truth

```text
authorities/records/<issuer>/<authority-id>.json
```

Each record contains stable identity/discovery metadata only. Versioned standards use version-specific IDs. Rolling provider/policy pages use `identityMode=rolling-source`.

### Currentness observations

```text
authorities/observations/<authority-id>/<YYYY-MM-DD>.json
```

Currentness is append-only evidence separate from authority identity. A newer observation does not rewrite the historical observation.

### Generated discovery index

```text
authorities/generated/authority-index.json
```

The index is disposable and reproducible. It contains only Level-0 discovery metadata and exact source digests. Delete it and rebuild it at any time.

### Progressive loading

- **Level 0 — discovery index:** id, title, issuer, kind, version, aliases/topics, latest lifecycle observation.
- **Level 1 — authority record:** official source, identity mode, relations, access boundary and registration provenance.
- **Level 2 — task-local Standard-Native profile:** BOUND/EXCLUDED/DEFERRED role, applicability rationale, requirements, claim boundary and evidence expectations.
- **Level 3 — external source/full text:** official web source or lawfully accessed licensed material. The catalog does not copy standards text.

## Commands

```bash
python scripts/authority_catalog.py build
python scripts/authority_catalog.py list
python scripts/authority_catalog.py find "risk management"
python scripts/authority_catalog.py show iso-31000-2018
python scripts/authority_catalog.py refresh iso-31000-2018
```

`refresh` is intentionally read-only. It emits the exact official source and latest observation plus instructions for a semantic currentness check. It does not infer status from HTTP reachability and does not mutate records.

There is intentionally no `authority apply` command. Catalog discovery has no authority to decide applicability.

## Growth policy

The initial broad seed phase closed on 2026-09-14. From that point, catalog growth is **task-driven**, not enumeration-driven.

Register or refresh an authority when at least one of these is true:

1. an active task, Standard-Native profile, or capability package names an external authority that the catalog cannot resolve precisely;
2. exact edition/version/currentness materially affects verification or delivery;
3. repeated cross-domain use makes Level-0 discovery materially useful;
4. an already registered authority is revised, superseded, withdrawn, or otherwise changes lifecycle state.

Do **not** add a record merely because a standard, framework, provider, taxonomy, platform, or body of knowledge exists. Broad families must normally resolve to the concrete authority actually required by the workload. Providers and tools remain provider records unless their independent specification is itself needed as semantic authority.

Discovery is fail-closed for multi-token semantic queries: every meaningful query token must be represented by a candidate. Generic modifiers such as `latest`, `official`, or `standard` do not relax semantic identity. An empty result means **not registered / not resolved**, not that a vaguely similar authority should be substituted.

Seed closure evidence: `evidence/acceptance/authority-catalog-seed-closure-20260914.json`.

## Non-goals

R1 deliberately does not add:

- a registry daemon or microservice;
- PostgreSQL or a vector database;
- standard full-text ingestion;
- automatic applicability decisions;
- a global Research/Security/Game standard bundle;
- credentials or licensed source material;
- a universal compliance/verdict model;
- auto-upgrade of task profiles to a newer edition;
- an Ordivon-private standard identifier replacing the external identity.

## Trust and licensing

Catalog metadata is a project-controlled trust input. Official external sources remain authoritative. Store only metadata, lawful references and permitted derived mappings. Do not commit licensed standards text, account cookies, API credentials or provider secrets.
