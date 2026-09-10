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

Distribution does not own a generic retry-state machine before a real dispatch consumer earns one. Blind resend after an ambiguous external write is forbidden by contract: a dispatcher may retry only when its provider/effect-specific semantics prove the same logical effect is idempotent, or when provider-native reconciliation proves that the original effect was never applied. A transport/runtime success, a free-form `published` label, or the local `delivery_key` alone never grants resend or acceptance authority. Carrier-effect acceptance is owned exclusively by the provider-native verification boundary below. Outcome evidence deliberately does not publish a generic `deliveryTerminal` decision: provider state is an observation, while terminality/requery/replay is provider/effect-relative dispatcher policy.

Every public/destructive plan must bind an exact occurrence before dispatch: opaque account identity + exact artifact digest + effect + intent ID. The resulting `delivery_key` is carried into provider observations and natural-episode evidence. It is a reconciliation coordinate only; it is never treated as proof that the provider implements idempotency. A provider outcome with a different delivery key or artifact digest cannot be reused to satisfy the plan.

## Acceptance

The narrow carrier acceptance boundary requires:

- exact carrier profile identity/currentness;
- exact effect + delivery key + artifact digest;
- provider object identity;
- provider-native read-back as the status source;
- an effect-compatible terminal provider state.

For publication/correction, `published` can be an accepted carrier effect. For delete/withdraw, only provider-native `deleted`/`withdrawn` standing can accept that destructive effect. `acceptedPublication` remains narrower than `acceptedCarrierEffect`: deleting an object is a verified carrier consequence but never a publication.

Even then, the evidence proves only carrier effect standing. It does not prove content truth, audience reception, impact, goal completion or Distribution maturity.

## Natural-event rule

Distribution maturity must not be obtained by publishing something useless solely to create test evidence. A maturity episode can be bound only when:

- the public/destructive effect served a real independent goal (for example, a genuine release announcement or a real correction/withdrawal);
- the plan was `ready`, with no unresolved provider authority or per-effect interaction gate;
- the exact effect had explicit user authority;
- plan and provider evidence match on carrier, effect, delivery key and artifact digest;
- provider-native accepted carrier effect was observed;
- the episode is not tagged as an architecture/maturity/evidence-generating test.

A natural-episode object is still only domain evidence construction, not maturity authority. Before any D2/D3 aggregation, the exact episode evidence must cross the existing Artifact E2E attestation/trust boundary (in-toto/SLSA VSA and the configured authenticity policy). Distribution does not maintain a second local evidence-authenticity scheme.

This keeps the earlier GitHub D2 positive control while allowing future non-GitHub events to accumulate real cross-carrier evidence.

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

**D2 Verified Outcome** requires provider-native acceptance of a naturally useful real external effect, exact attested evidence, and an independent graduation judgment. Existing GitHub evidence remains bounded to GitHub. Generic/cross-carrier D2 needs at least one real non-GitHub episode; caller-authored mappings are not maturity evidence.

**D3 Persistent Capability** requires repeated non-identical real episodes across multiple carrier contexts **plus effect variation and real recovery/correction/withdrawal evidence**, with bounded currentness, authority handling and Human Mechanical Actions. Repetition alone is insufficient; three local fixtures do not count. Distribution deliberately does not expose a generic local `maturity_observation()` aggregator: D3 evidence must be assembled from Artifact-E2E-verified attestations and adjudicated under the assurance policy rather than inferred from unauthenticated Python mappings.

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
