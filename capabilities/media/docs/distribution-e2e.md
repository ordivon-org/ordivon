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

When an external provider requires human UI completion, Distribution returns a bounded `user_action_required` handoff instead of impersonating automation.

## Ambiguous outcomes

Blind resend is forbidden. If the provider state is `submitted`, `processing` or `unknown`, the next action is provider-native read-back/reconciliation. `published` is terminal for the attempted publication and must not be resent. Rejected/withdrawn/deleted objects require a **new explicit intent** before another external write.

The local `delivery_key` binds carrier + opaque account identity + artifact digest + effect + intent ID. It is a reconciliation coordinate only; it is never treated as proof that the provider implements idempotency.

## Acceptance

The narrow carrier acceptance boundary requires:

- exact carrier profile identity/currentness;
- exact artifact digest;
- provider object identity;
- provider-native read-back as the status source;
- provider state `published`.

Even then, the evidence proves only carrier publication standing. It does not prove content truth, audience reception, impact, goal completion or Distribution maturity.

## Natural-event rule

Distribution maturity must not be obtained by publishing something useless solely to create test evidence. A maturity episode can be bound only when:

- the public effect served a real independent goal (for example, a genuine release announcement or an authorized paper/publication event);
- the exact effect had explicit user authority;
- provider-native publication acceptance was observed;
- the episode is not tagged as an architecture/maturity/evidence-generating test.

This keeps the earlier GitHub D2 positive control while allowing future non-GitHub events to accumulate real cross-carrier evidence.

## Current carrier observations — 2026-09-10

These are dated observations and must be re-observed before a live effect. The code profile records the source URLs and does not claim that provider policy is durable.

| Carrier | Current write standing used by Distribution | Critical authority/acceptance boundary |
| --- | --- | --- |
| GitHub | available if authorized | existing bounded positive control; provider object/read-back |
| X | API available if authorized and current API access exists | developer app + user OAuth + current API access; provider-native read-back; edit only when provider edit controls allow it (30-minute window, up to 5 edits, new ID per edit) |
| TikTok | Content Posting API after product/scope/user auth; public path also requires client audit | creator/user-visible consent + publish/status ID; submitted/private-restricted is not public acceptance |
| Douyin | Open Platform after permission review + user authorization | each publish-on-behalf action must remain user-perceivable; provider review/status is distinct from publication |
| Bilibili | Open Platform after identity/application/content-distribution qualification | manuscript/provider identity + status/data return |
| Reddit | approval-constrained | current Responsible Builder / app or Devvit approval + user action permission; do not assume legacy unrestricted API access |
| Xiaohongshu | no generally available note-write API observed | `write_notes` is planned/restricted; use bounded human handoff rather than inventing API authority |
| YouTube | Data API if authorized; public upload has project audit constraints | OAuth + provider video identity + processing/visibility read-back |

## D1 / D2 / D3 / DEFAULT

**D1 Complete One-shot Delivery substrate** is supported only when one carrier can be planned end-to-end with exact artifact identity, explicit authority, dispatch adapter, provider-state reconciliation, read-back and correction/withdrawal semantics. Local profile/state-machine tests alone are construction evidence, not a real delivery.

**D2 Verified Outcome** requires provider-native acceptance of a naturally useful real external effect. Existing GitHub evidence remains bounded to GitHub. Generic/cross-carrier D2 needs at least one real non-GitHub episode and an independent graduation judgment.

**D3 Persistent Capability** requires repeated non-identical real episodes across multiple carrier contexts with bounded recovery, currentness, authority handling and Human Mechanical Actions. Three local fixtures do not count.

**DEFAULT** is a separate adjudication: sufficient D3 evidence must show that Distribution can normally be selected without treating the path as an experiment. `maturity_observation()` deliberately never sets `defaultClaimed=true`.

## Falsifiers

Reopen or narrow this profile if any of the following occurs:

- provider policy/current API no longer matches a dated profile;
- one platform requires a genuinely irreducible semantic primitive that cannot be represented as carrier context + current Media foundations;
- real delivery repeatedly needs hidden global scheduling/transaction semantics rather than thin provider adapters over existing Runtime/Host/Workstation substrate;
- provider read-back cannot distinguish submission/processing/publication, requiring a narrower claim ceiling;
- user authorization or platform policy cannot be represented without unsafe reusable authority;
- correction/delete semantics differ from the profile and could cause destructive mistakes;
- natural real episodes fail despite all local contract tests.
