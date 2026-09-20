# NDSA 2.1 Preservation Gap Projection — Data Lifecycle R1

This is not a formal score or certification. NDSA Levels 2.1 is used as a maturity/gap owner.

| Area | Evidence standing | Residual gap |
|---|---|---|
| Storage | PARTIAL | Two exact AIP copies exist, but both share one host/WSL failure domain. |
| Integrity | STRONG_LOCAL | 49/49 source fixity, AIP validation, scheduled Fixity client, master/replica equality. Provider liveness can interrupt scans. |
| Control | PARTIAL | Provider/Storage Service boundaries and root-owned fixity credentials exist; full preservation access-control audit is outside R1. |
| Metadata | STRONG_LOCAL | E-ARK + METS/PREMIS + source identity/contracts/lineage are preserved. Rights/retention remain upstream gaps. |
| Content | PASS_SELECTED_CORPUS | Raw/derived/runtime evidence is preserved for the selected pilot, not yet all domains. |
| Sustainability | NOT_ASSESSED | NDSA 2.1 sustainability guidance has not yet been evaluated for this deployment. |

The immediate preservation next step is not another local copy. It is an independent failure-domain/offsite copy when an approved target is available.
