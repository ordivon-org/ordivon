# World retirement — new Ordivon model

Source authority observed before archive: `/root/projects/ordivon-world@4f908b237d45a8e8759bfdf3ec41dab8e4b73948`

Archive commit: `feb89ee42503e70b49da181ac5a6b6486aa04b0e`

Closeout date: 2026-09-13

## Historical responsibility

World combined external-provider request binding/reconciliation, response-loss handling, temporal evidence, Resource/Message/Entity trajectory experiments, and a co-located Cloudflare Edge provider.

## Current classification

**ARCHIVE WORLD OWNER + RETAIN CONCRETE PROVIDER UNDER OPERATIONS.**

The generic World owner/product boundary is not retained. New external effects should start from the concrete provider/system and consuming domain rather than route through a permanent World abstraction.

## Cloudflare provider disposition

The one live operational blocker was the Cloudflare Edge provider. It was extracted from the historical World repository, validated independently, then absorbed into the maintained Operations project:

- maintained source: `/root/projects/ordivon-workstation-v2/providers/cloudflare`
- Operations absorption commit: `7371f9f149b02b88f4a720f602e70944318e7611`
- short-lived staging history retained in Operations ref: `refs/ordivon/migration/cloudflare-provider-staging`
- top-level staging repository `/root/projects/ordivon-cloudflare-provider` was removed after live cutover
- installed controllers and `ordivon-edge-gc.service` now bind the Operations path
- post-cutover read-only Edge health remained `status=ok` with the existing provider policy/capability state

Operations owns source maintenance, installation, systemd realization, policy/config materialization, upgrade/rollback/GC tooling, and health/SLO plumbing. Cloudflare remains authoritative for Worker/R2/request/receipt truth. Consuming domains retain intent, authorization, semantic verification, and completion meaning.

## Retained World value

Preserve `ordivon-world` as historical provenance/reproducibility evidence, especially:

- response-loss, idempotency, retry/reconciliation lessons;
- provider occurrence vs Task completion boundaries;
- historical-vs-current-state distinctions;
- temporal provenance/evidence work;
- Resource / Message / Entity trajectory experiments and negative results;
- high-pressure deletion evidence for abstractions that did not justify survival;
- final contracts, fixtures, tests, and the historical co-located Cloudflare snapshot.

Do not bulk-import World ontology/contracts into Ordivon Next.

## Dependency/validation evidence

- current-consumer census found no active code consumer requiring the World package in the current Ordivon projects surveyed;
- the Cloudflare provider operational dependency was moved to Operations before archive;
- World archival validation passed its locked owner environment, Ruff, 130 unit tests, contract checks, and documentation checks;
- no Cloudflare remote mutation was required for the source-home migration.

## Forward route

`domain intent -> concrete provider/system -> exact idempotency/reconciliation contract -> provider/domain evidence -> verification`

Create a shared cross-provider abstraction only when multiple real consumers demonstrate an irreducible common responsibility.

## Disposition

- active World owner: **NONE**
- generic external-world routing layer: **REJECTED**
- World source repository: **ARCHIVE / HISTORICAL CORPUS**
- Cloudflare provider maintenance: **OPERATIONS v2**
- provider-native remote truth: **CLOUDFLARE / PROVIDER-NATIVE**
- consuming-domain semantic authority: **CONSUMER-OWNED**
