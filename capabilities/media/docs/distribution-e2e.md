# Distribution E2E

## Standing

Distribution is the relation between a produced artifact and an external carrier/context. It is **not** a new foundational medium and a carrier is not a substitute for the Media foundations used to make the artifact.

This profile exists to make one delivery chain explicit:

```text
Intent
  -> Artifact identity
  -> Carrier capability/currentness
  -> Account/provider authority
  -> Exact public-effect authority
  -> Dispatch
  -> Provider processing/review
  -> Provider-native read-back
  -> Accepted carrier object
  -> Feedback/correction/withdrawal
  -> Goal-relative consequence
```

A process exit, HTTP 2xx, upload receipt, provider submission identifier, or local Runtime success is not publication acceptance by itself.

## Ownership split

- **Media** owns carrier-neutral Distribution semantics: carrier profiles, artifact/effect intent, authority requirements, provider state, acceptance, correction/withdrawal, feedback evidence and goal-relative natural-episode binding.
- **Workstation** owns local execution mechanics already present there: credentials/material census, OAuth callback handling, browser/headful human handoff, network path/currentness and bounded external execution.
- **Web** remains an external consumer/owner. Distribution must not absorb the Web product simply because browsers are one encounter/distribution context.
- Provider-specific adapters should remain thin. They must not grow a second scheduler, database, generic workflow system or hidden authority model.

## Authority model

Every public or destructive effect is gated independently across three classes:

1. **Reusable provider/account authority**: the current app, scope, account, billing, review or qualification required by the provider.
2. **Per-effect provider interaction**: current creator-info/metadata/consent or explicit manual/perceivable action that the provider requires for this specific effect. These are not stored as reusable OAuth authority.
3. **Exact Ordivon user effect authority**: the user authorized this concrete public effect, not merely the existence of a reusable credential.

A reusable OAuth token therefore does not imply permission to publish arbitrary future content. TikTok creator-info/metadata/explicit consent, Douyin per-post perceptibility and Reddit explicit manual user action are represented as per-effect interactions rather than reusable grants.

Provider/account authority is also **effect-specific**. Read-back/status paths request the smallest observed read authority rather than inheriting publication scopes merely because the same carrier supports writes. For example, X read-back uses a read scope rather than `tweet.write`, YouTube read-back does not request `youtube.upload`, and Douyin read-back uses video list/data permission instead of `video.create`. Carrier-level authority lists remain conservative inventory views, not the planner's minimum request set.

When an external provider requires human UI completion, Distribution returns a bounded `user_action_required` handoff instead of impersonating automation.

## Ambiguous outcomes

Distribution does not own a generic retry-state machine before a real dispatch consumer earns one. Blind resend after an ambiguous external write is forbidden by contract: a dispatcher may retry only when its provider/effect-specific semantics prove the same logical effect is idempotent, or when provider-native reconciliation proves that the original effect was never applied. A transport/runtime success, a free-form `published` label, or the local `delivery_key` alone never grants resend or acceptance authority. Provider-state reconciliation and acceptance are owned by the actual provider adapter/transport boundary; this carrier-neutral module does not self-attest them from caller-authored mappings.

Every public/destructive plan must bind an exact occurrence before dispatch: opaque account identity + exact artifact digest + effect + intent ID. The resulting `delivery_key` is carried into provider adapter requests/read-back evidence. It is a reconciliation coordinate only; it is never treated as proof that the provider implements idempotency, as a provider precondition, or as proof that a response came from the provider.

### Supersession and current desired state

A Distribution plan is an immutable effect occurrence, not a mutable desired-spec object. Changing the intended occurrence requires a new exact identity coordinate (for example a new `intentId`, artifact, effect, or account), which changes the `delivery_key`; an outcome from the old occurrence therefore cannot satisfy the new plan. A later correction/delete/withdrawal is a new exact occurrence and does not erase the historical fact that an earlier provider effect occurred.

Distribution deliberately does not define its own `desiredRevision`, `generation`, or `observedGeneration` field. Those mechanisms are appropriate at an owner that actually maintains mutable desired state (analogous to conditional-update/resource-generation patterns); that owner must fence stale state before selecting the exact Distribution plan. The local `delivery_key` remains occurrence identity only and must not be promoted into a provider precondition, provider idempotency token, or global currentness authority.

## Observation authority and acceptance

`acceptanceEvidence` in a carrier profile is a **requirement inventory**, not evidence that the requirement has been satisfied. Distribution core deliberately exposes no pure `verify_provider_outcome()` or `bind_natural_episode()` helper: ordinary Python mappings, object IDs and labels such as `provider-native-readback` cannot prove their own external origin.

A real carrier adapter must establish observation authority using the strongest provider-native mechanism actually available: for example an authenticated API request/response bound to the expected account/object/effect, or a provider webhook/event whose signature/MAC is verified at the receive boundary. If the provider supplies an end-to-end message signature, the adapter may use the applicable signature standard and policy rather than inventing an Ordivon signature format. The resulting exact evidence should cross the existing Artifact E2E provenance/attestation boundary before it contributes to D2/D3 adjudication.

Authenticity, point-in-time state and completeness are separate properties. A valid webhook signature can show who sent one payload without proving that no deliveries were missed or that it is the latest object state. A successful authenticated GET can establish an exact object snapshot without proving collection completeness. Negative/collection claims require the provider's own pagination, cursor/sequence, list+watch, snapshot token or equivalent continuity semantics where available. Distribution must not normalize those provider-specific guarantees into a generic `complete=true` flag until a real cross-carrier consumer earns such a law.

## Natural-event evidence

A useful real public effect remains the right source of maturity evidence, but this module does not manufacture a natural-episode evidence object from local mappings. The provider adapter must first establish authentic provider observation for the exact occurrence; Artifact E2E then binds provenance/attestation; an assurance/adjudication layer may decide whether that evidence contributes to D2/D3. Publishing something solely to manufacture maturity evidence remains prohibited.

## Current carrier observations — 2026-09-10

These are dated observations and must be re-observed before a live effect. The code profile records the source URLs and does not claim that provider policy is durable.

| Carrier | Current write standing used by Distribution | Critical authority/acceptance boundary |
| --- | --- | --- |
| GitHub | available if authorized | existing bounded positive control; provider object/read-back |
| X | API available if authorized and current API access exists | effect-specific OAuth scopes (`tweet.write` for writes, read scope for read-back) + provider-native read-back; edit only when provider edit controls allow it (30-minute window, up to 5 edits, new ID per edit) |
| TikTok | Content Posting API after product/scope/user auth; public path also requires client audit | creator/user-visible consent + publish/status ID; submitted/private-restricted is not public acceptance |
| Douyin | Open Platform video/image creation after permission review + user authorization | `video.create` for create, list/data permission for read-back; each publish-on-behalf action remains user-perceivable; provider review/status is distinct from publication |
| Bilibili | Open Platform after identity/application/content-distribution qualification | manuscript/provider identity + status/data return |
| Reddit | approval-constrained | current Responsible Builder / app or Devvit approval + user action permission; do not assume legacy unrestricted API access |
| Xiaohongshu | no generally available note-write API observed | `write_notes` is planned/restricted; use bounded human handoff rather than inventing API authority |
| YouTube | Data API if authorized; public upload has project audit constraints | OAuth + provider video identity + processing/visibility read-back |

## D1 / D2 / D3 / DEFAULT

**D1 Complete One-shot Delivery substrate** is supported only when one carrier can be planned end-to-end with exact artifact identity, explicit authority, dispatch adapter, provider-state reconciliation, read-back and correction/withdrawal semantics. Local profile/state-machine tests alone are construction evidence, not a real delivery.

**D2 Verified Outcome** requires provider-adapter-established observation authority for a naturally useful real external effect, exact Artifact-E2E-attested evidence, and an independent graduation judgment. Existing GitHub evidence remains bounded to GitHub. Generic/cross-carrier D2 needs at least one real non-GitHub episode; caller-authored mappings or self-declared source labels are not maturity evidence.

**D3 Persistent Capability** requires repeated non-identical real episodes across multiple carrier contexts **plus effect variation and real recovery/correction/withdrawal evidence**, with bounded currentness, authority handling and Human Mechanical Actions. Repetition alone is insufficient. Distribution exposes neither a local outcome-verification shortcut nor a generic maturity aggregator; D3 evidence must be assembled from provider-authoritative observations plus Artifact-E2E-verified attestations and adjudicated under the assurance policy.

**DEFAULT** is a separate adjudication: sufficient D3 evidence must show that Distribution can normally be selected without treating the path as an experiment. No local Distribution helper can set or imply DEFAULT.

## Falsifiers

Reopen or narrow this profile if any of the following occurs:

- provider policy/current API no longer matches a dated profile;
- one platform requires a genuinely irreducible semantic primitive that cannot be represented as carrier context + current Media foundations;
- real delivery repeatedly needs hidden global scheduling/transaction semantics rather than thin provider adapters over existing Runtime/Host/Workstation substrate;
- provider read-back cannot distinguish submission/processing/publication, requiring a narrower claim ceiling;
- user authorization or platform policy cannot be represented without unsafe reusable authority;
- correction/delete semantics differ from the profile and could cause destructive mistakes;
- natural real episodes fail despite all local contract tests.
