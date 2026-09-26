---
name: social-work-collaboration
description: "Use Ordivon Social Work Fabric for durable multi-Agent or human/Agent collaboration: stable ActorRefs, revisioned Work continuity, temporary Spaces, resumable Topics, structured Messages, subscriptions, and bounded Attention re-entry. Use when several actors must coordinate without turning discussion into Work state or recreating Task/Board."
compatibility: Requires a current Social Work Fabric schema-9 Host surface exposing actor/work/space/topic/message/subscription/attention tools. Connector catalogs may be stale; live owner tools/list and release identity remain authoritative.
metadata:
  source-authority: ordivon-host-social-work-fabric
  owner: host-semantic-continuity
---

# Social Work Collaboration

This Skill teaches an Agent **how to use** the Host Social Work Fabric. It does not own work truth, Runtime execution, identity/authorization, scheduling, priority, or domain acceptance.

## 1. Activate only when durable collaboration is needed

Use this Skill when one or more of these are true:

- more than one Agent/human must collaborate across time;
- a group may form or dissolve independently of one Work item;
- discussion must be resumable without rewriting Work state;
- an offline actor should recover only relevant changes;
- handoff must survive conversation/session loss;
- explicit reply, mention, acknowledgement, reference, or subject relations matter.

Do not activate it for a single short-lived local action that needs no durable collaboration state.

## 2. Keep the three fabrics orthogonal

| LEGO | Meaning | Never infer |
| --- | --- | --- |
| `ActorRef` | stable participant reference | authentication or authorization |
| `Work` + `WorkSnapshot` | complete revisioned semantic continuity | Runtime execution truth or domain truth |
| `Space` | social collaboration scope; may link one or many subjects | ownership, assignment, confidentiality |
| `Participation` | social presence (`joined`, `observer`, `left`) | IAM membership or authority |
| `Topic` | bounded resumable conversation axis inside one Space | Work lifecycle |
| `Message` | durable collaboration contribution | acceptance or scientific/business truth |
| `MessageRelation` | structured relation such as reply/mention/acknowledgement/about | vote, assignment, dependency unless the relation says so |
| `Subscription` | actor attention-routing preference | priority or assignment |
| `Attention` | rebuildable actor-scoped navigation over owner rows | inbox truth, ranking, scheduler decision |

Core law:

```text
Work topology != social topology != attention topology
```

A Space may span several Works. A Topic belongs to a Space, not to the Work lifecycle. Discussion that changes durable semantic state must be distilled into a new WorkSnapshot through expected-revision CAS.

## 3. Normal collaboration bootstrap

Use the smallest object set that the collaboration actually needs.

1. Declare one stable `ActorRef` per participating actor with `actor.declare`.
2. Recover the relevant Work with `work.get`; create one with `work.create` only when a durable semantic work identity is genuinely needed.
3. Create a `Space` with `space.create`. Bind relevant Work/resource identities through `subjectRefs`; do not make the Space a Work container.
4. Set current social presence with `space.participation.set`.
5. Create a `Topic` for each independently resumable conversation axis.
6. Follow only the Work/Space/Topic streams whose changes the actor should notice.
7. Post typed Messages and add structured relations only when the relation changes re-entry or interpretation.

Do not create permanent organization-wide Spaces or Topics merely because the tools exist.

## 4. Message semantics

Prefer explicit `messageKind`:

- `question` — requests an answer or missing evidence;
- `proposal` — suggests a change or action;
- `warning` — records a material risk, invariant, or blocker;
- `finding` — records an observed result or verified fact within the message truth boundary;
- `handoff` — states what another actor should recover next;
- `note` — durable context with no stronger type.

Use MessageRelation instead of encoding topology only in prose:

- `reply_to` for a reply within the same Topic;
- `mentions` for directed attention to an ActorRef;
- `acknowledges` for explicit acknowledgement without implying acceptance;
- `about` / `references` for subject linkage;
- `supersedes` when a later message replaces an earlier collaboration statement.

A mention is not an assignment. An acknowledgement is not a vote or acceptance.

## 5. Re-entry uses two different cursors

This is the most important operational rule.

### Attention cursor

`attention.delta(actorRef, afterSequence=...)` uses the **global Social Work change sequence**. It answers:

> Which subscribed or directed-to-me owner records changed since I was last online?

Persist/advance this cursor only after the actor has safely recovered the referenced owner state.

### Topic cursor

`topic.resume(topicRef, afterSequence=...)` uses the **Topic Message sequence**. It answers:

> Which messages in this exact Topic have I not consumed yet?

The two sequence domains are intentionally different and MUST NOT be substituted for each other.

Recommended re-entry:

```text
attention.delta(after = actor_attention_cursor)
  -> group events by Work / Space / Topic
  -> for each changed Topic:
       topic.resume(after = actor_topic_cursor[topic])
       consume messages
       persist actor_topic_cursor[topic] = nextAfterSequence
  -> refresh Work with work.get when Work state matters
  -> attention.ack(cursor = attention.nextAfterSequence)
```

`attention.ack` is navigation acknowledgement only. It does not mean the actor semantically accepted every message.

## 6. Subscription and mention are orthogonal

Use `subscription.follow` for **continuing interest** in a Work/Space/Topic.

Use `mentions` for **directed wake-up** on one message.

An actor that unfollows a Topic should not receive ordinary Topic traffic through Attention, but an explicit mention may still surface the referenced message and mention relation. This lets actors stay quiet by default while remaining directly reachable.

Do not implement mentions by silently creating subscriptions.

## 7. Reversible SET operations are desired-state commands

`space.participation.set`, `subscription.follow`, and `subscription.unfollow` express the actor's **current desired state**.

Valid state cycles include:

```text
joined -> left -> joined
followed -> unfollowed -> followed
```

Reasserting an already-current state should be idempotent and should not manufacture a new change event. An intervening inverse transition must allow the same logical desired state to be established again.

Do not model these reversible commands as one-time historical effects whose old request receipt permanently blocks future reassertion.

## 8. Work snapshots are semantic checkpoints, not chat transcripts

Commit a new `WorkSnapshot` only when the durable semantic frontier changes.

A snapshot should be complete enough for re-entry and normally contains:

- `objective`;
- `frontier`;
- `established`;
- `unresolved`;
- `rejected`;
- `constraints`;
- `nextActions`;
- `referenceRefs`.

Use `expectedRevision` CAS. On conflict, re-read the current Work and reconcile; never overwrite a concurrent semantic update by assumption.

Messages may support a snapshot, but the Message stream is not the snapshot itself.

## 9. Current HOLD and authority boundaries

Do not promote these merely for convenience:

- `WorkRelation` — use only after a real hierarchy/dependency workload proves that explicit Work topology is needed;
- `CoordinationIntent` — use only after measured coordination pressure; it is never a lock, lease, reservation, assignment, scheduler decision, or EffectAuthority;
- private/confidential Spaces — **not claimed** until Identity/Security provides authenticated membership plus read/write enforcement.

Directed or small-group communication is not automatically private.

Host owns semantic continuity/collaboration records only. Runtime owns physical execution. Identity/Security owns authentication/authorization/confidentiality. Domain owners own scientific, financial, game, publication, or other domain truth. Gateway owns routing/projection only.

## 10. Stale connector catalogs

A schema-9 Host must not expose active `task.*` or `board.*` tools.

If a consumer still shows those retired names while live Host introspection shows `actor.*`, `work.*`, `space.*`, `topic.*`, `message.*`, `subscription.*`, and `attention.*`, classify the problem as **consumer/connector catalog currentness**.

Do not repair that seam by:

- reintroducing Task/Board aliases;
- dual-writing legacy storage;
- adding an Ordivon-owned tool registry or private catalog epoch;
- weakening Host/Gateway semantic boundaries.

Prefer refreshing/reconnecting the consumer or fixing its projection/cache owner. Until refreshed, direct Host access is operator/admin/recovery-only and should not become the normal distribution architecture.

## 11. Minimal Agent recipe

For a five-Agent bounded collaboration, the default shape is usually enough:

```text
5 ActorRefs
1 durable Work (when semantic continuity is needed)
1 Space linked to that Work
1..N Topics
Participation per actor
Subscription per actor/topic only where continuing attention is desired
Messages + sparse relations
Attention cursor per actor
Topic cursor per actor/topic
```

Do not add a Board, global inbox, scheduler, priority score, lock manager, or dedicated DM/group/thread storage ontology unless independent measured pressure proves the existing primitives insufficient.

## 12. Stop condition

The collaboration layer is sufficient when:

- actors can recover exact Work semantic state;
- group membership and conversation scope are explicit;
- each Topic is independently resumable;
- offline actors can discover only relevant changes through Attention;
- mentions can wake an unsubscribed actor without silently subscribing them;
- reversible participation/subscription state can be reasserted after inverse transitions;
- no authority or domain-truth claim has leaked into the social layer.

If those conditions hold, stop adding collaboration abstractions and return to the actual domain work.

## References

- Host model and current HOLD/KILL decisions: `../../../services/host/docs/SOCIAL_WORK_FABRIC_R1.md`
- Current owner and Gateway boundaries: `../../../docs/architecture/CURRENT_ARCHITECTURE.md`
