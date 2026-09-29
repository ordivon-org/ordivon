# Ordivon Agent Birth — Perceptual Closeout Gap Map R1

Date: 2026-09-26

## Scope

This note records only the Agent Birth deltas required to execute three independent exact-byte perceptual observers for Paper-3 C21. It does not redesign Agent Birth, reopen Paper-3 science, or weaken provider-effect fencing.

## Current LEGO chain

`CampaignSpec -> deterministic role/effect identity -> Campaign Registry -> Temporal child workflow -> carrier serialization -> provider boundary -> effect ledger -> exact conversation binding -> post-Birth output observation -> carrier release -> observer receipt validation`

## Gap / resolution matrix

| ID | LEGO | Fresh gap | Resolution in this change | Acceptance |
|---|---|---|---|---|
| AB-G1 | Exact input binding | Campaign/Carrier/UI path admitted at most one attachment; blind reviewer requires exact PDF + exact R10 ZIP. | Raise bounded attachment set to four; preserve digest-set identity, per-file digest verification, unique path/name constraints, 100 MiB/file and 200 MiB aggregate staging limits; upload each manifest entry sequentially. | Two-file request changes effect identity and reaches one frozen manifest; tests pass. |
| AB-G2 | ConversationOutputObserver / AB34 | Browserless had a lower-level read-only output script, but the production Windows normal-Chrome carrier had no equivalent read-back path. | Add exact target/effect-bound `observe` mode to the existing Windows driver and Gateway controller; it requires the exact conversation URL, exact effect marker and explicit output begin/end markers; it reports `providerEffectAttempted=false`, `composerFilled=false`, `sendAttempted=false`. | CAPTURED receipt is identity-bound and carries assistant-output digest; non-CAPTURED receipts expose no output. |
| AB-G3 | Carrier lifecycle | Normal-Chrome materialization deliberately refuses takeover when Chrome already exists, but successful Birth left its Chrome carrier alive, blocking the next independent Birth. | Add exact-target `release` mode. It refuses release before completed output marker, on target drift, or on ambiguous main-window cardinality; after verification it releases only the current carrier generation. | Release receipt is no-SEND, exact-target bound and idempotent via ALREADY_RELEASED. |
| AB-G4 | Public semantic surface | Agent Automation MCP could launch/census/reconcile/continue but could not retrieve a completed Birth output or release the completed Windows carrier. | Add `conversation.output` and `conversation.release` semantic tools backed by registered Campaign bytes and bound providerResource; no raw spec paths are exposed. | MCP catalog test includes both tools; read/write annotations preserve the authority distinction. |
| AB-G5 | Independent observer occurrence | Paper-3 packets existed but 0/3 independent agent occurrences had been created. | Execute three separate one-agent Campaigns, never one three-role shared conversation. Each has a distinct campaignId/agentId/effectId/providerResource and receives only its role packet plus exact required carrier(s). | Three distinct Birth occurrences + no cross-receipt exposure + exact-byte observer receipts. |

## Preserved invariants

- Effect identity remains deterministic over Campaign/role/prompt/attachment-set bytes.
- Attachment upload remains inside the fenced provider effect; ambiguous post-effect failures are never blind-retried.
- Temporal remains the durable workflow/retry owner.
- Provider CHALLENGE_GATED observations remain HOLDs. Browserless profiles are not rotated/restarted/cleared to bypass provider policy.
- `conversation.output` is observation only; it cannot fill the composer or SEND.
- `conversation.release` mutates local carrier lifecycle only after exact target and completed-output proof; it does not alter conversation content.
- Three perceptual observers are separate Birth occurrences. The same closeout agent does not manufacture three receipts.

## Residual boundary

The three occurrences may use the same authenticated provider account/profile because current production has one normal-Chrome user-browser carrier. Independence is therefore defined as distinct provider conversations/effect identities with no cross-receipt exposure, not as three different provider accounts. Paper-3 acceptance must continue to enforce distinct observer occurrence identities and exact-byte receipts.
