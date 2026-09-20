# Live Test Account — Local Admission Handoff

Status: **RETIRED 2026-09-14**.

The former local admission runner was a transitional bridge into legacy `ordivon-finance` observer/admission scripts. It has been removed from the forward Market Capital surface.

Current architecture requires read-only private Reality to graduate independently before any order-capable credential or external financial write path is admitted. `config/execution_authority.json` remains `NON_LIVE`, and `config/live_test_account_policy.json` keeps `orderSubmissionAdmission=NOT_ADMITTED` and binds no executor credential path.

Read-only observer credentials remain external to this repository and are governed by `config/private_reality_policy.json`. Mature provider clients remain the selected substrate for future provider-native observation. A future external-write lane must establish a new current provider/executor admission surface under the Market Capital authority boundary; it must not revive this retired Finance-repository handoff.

Historical evidence about the old runner remains available in Git history. Its existence never constituted production-trading authority.
