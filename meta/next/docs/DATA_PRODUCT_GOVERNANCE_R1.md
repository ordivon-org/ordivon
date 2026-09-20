# Data Product Governance R1

Date: 2026-09-20

## Scope

R1 adds fail-closed governance to the two domain-owned data products without inventing a new Ordivon rights, privacy, or retention language.

External owners:

- W3C ODRL 2.2: machine-readable rights-policy expressions;
- NIST Privacy Framework 1.0: current published privacy-risk baseline;
- ISO 15489-1:2016: records-management requirements and disposition context;
- ODPS 1.1.0: domain/team ownership and product metadata;
- DCAT 3: federated discovery and policy linkage.

NIST Privacy Framework 1.1 is not treated as final. As of 2026-09-20 NIST still describes the final 1.1 as coming soon.

## Owner versus rights holder

Both products now use the ODPS `team` field for the domain-level product owner.

The ownership scope is intentionally bounded to:

`PRODUCT_METADATA_AND_LIFECYCLE`

It does not assert intellectual-property ownership or redistribution rights over the underlying research dataset or provider market data.

## Fail-closed rights

No authoritative dataset license or provider redistribution grant was found in the selected frozen evidence.

Therefore each domain owns an ODRL `Set` policy that prohibits:

- `distribute`;
- `grantUse`;
- `delete`.

The first two prevent public accessibility from being silently promoted into third-party redistribution rights.

The temporary delete prohibition is not a permanent-retention decision. It prevents automated disposition while no applicable retention schedule has been established.

## Privacy boundary

Research:

- privacy assessment status: `NOT_FORMALLY_ASSESSED`.

Finance:

- existing evidence proves broker credentials were not used;
- private account data was not used;
- external financial writes were not attempted;
- broader privacy assessment remains incomplete.

Those bounded observations are not promoted into a claim of complete privacy compliance.

## Retention boundary

Retention schedule status for both products is:

`UNASSIGNED`

No arbitrary number of days or years is encoded.

Under ISO 15489, the next legitimate step is to identify the applicable research/business/legal records requirements and then replace the temporary no-delete policy with an authorized disposition rule.

## Federation

The DCAT catalog now types each product dataset as both:

- `dcat:Dataset`;
- `odrl:Asset`.

Each asset links to exactly one domain policy with `odrl:hasPolicy`.

The central catalog does not copy or become the owner of the policy.

## Standing

`PASS_FAIL_CLOSED_TWO_DOMAIN_RIGHTS_RETENTION_PRIVACY_BOUND`

This closes the unsafe-default P0. It does not resolve the underlying source licenses, complete a formal privacy assessment, or assign retention schedules. Those remain explicit P1 obligations.
