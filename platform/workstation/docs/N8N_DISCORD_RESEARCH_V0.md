# n8n Discord Research V0

Status: SOURCE CANDIDATE / LIVE AUTHORITY NOT YET BOUND

## Purpose

This is the thinnest read-only integration slice for scoped Discord community research:

```text
Research route / bounded caller
  -> CloudEvents request
  -> n8n webhook
  -> validate + build Discord Search Guild Messages URL
  -> HTTP Request with n8n-owned Discord Bot credential
  -> normalize provider result
  -> CloudEvents result
```

It is not a Discord account controller, archive service, RAG system, workflow authority, or research-validity owner.

## Authority boundary

- Discord owns message/permission/search truth.
- Human/operator owns bot installation and guild/channel permission consent.
- n8n owns the encrypted Discord credential, workflow definition, and execution history.
- Research owns semantic routing and research adequacy.
- Gateway/Runtime may invoke this workflow but do not gain Discord permission authority.
- This workflow never sends, edits, reacts to, or deletes a Discord message.

The source template is intentionally `active:false` and contains no credential ID. The HTTP Request node selects n8n's predefined `discordBotApi` credential type, but live credential ID/name binding is a deployment-time owner operation after BF1 authority currentness is established. Secret bytes must never be injected into workflow parameters, Git, Host messages, or generic evidence receipts.

## Deployment binding

The canonical workflow source deliberately contains no environment-specific credential object.

After BF1 creates one live n8n `discordBotApi` credential, the Workstation-owned convergence path is:

```bash
sudo ORDIVON_DISCORD_N8N_CREDENTIAL_NAME=ordivon-discord-research-v0 \
  ./platform/workstation/scripts/converge-n8n-discord-research-v0.sh
```

The convergence script reads only the credential metadata tuple `id/name/type`, requires exactly one matching `discordBotApi` credential, creates a mode-0600 transient import JSON with the n8n credential reference, imports/publishes the stable workflow ID, restarts the existing rootless n8n pod, and waits for readiness.

It never selects or prints the encrypted credential payload or Bot token. Missing/ambiguous credentials fail before import/publish.

This deployment success is still not Discord or Research semantic qualification. BF4 must execute the live provider canaries separately.

## Request contract

CloudEvent type:

`io.ordivon.research.community.discord.search.request.v1`

Required data:

- `authorityRef`: opaque current authority evidence reference; it is provenance, not a bearer credential.
- `guildId`: exact target guild snowflake.
- `channelIds`: explicit non-empty channel filter, max 500. V0 does not admit whole-guild unfiltered search.
- `content`: non-empty lexical query, max 1024. V0 deliberately rejects broad content-free enumeration.

Optional filters mirror a bounded subset of Discord Search Guild Messages: `authorIds`, `mentions`, `repliedToUserIds`, `has`, `pinned`, `mentionEveryone`, `minId`, `maxId`, `limit`, `offset`, `sortBy`, and `sortOrder`.

`includeNsfw=true` is rejected in V0.

The machine-readable contract is `n8n/contracts/ordivon-discord-research-v0.schema.json`.

## Result contract

CloudEvent type:

`io.ordivon.research.community.discord.search.result.v1`

Typed status:

- `OK`: provider HTTP 200 with normalized source-bound messages.
- `INDEXING_RETRY`: provider HTTP 202; `retryAfterSeconds` is projected when present.
- `RATE_LIMITED`: provider HTTP 429; retry timing is projected, not blindly retried.
- `DENIED`: provider HTTP 403.
- `PROVIDER_REQUEST_REJECTED`: provider HTTP 400.
- `NOT_FOUND`: provider HTTP 404.
- `PROVIDER_UNAVAILABLE`: provider HTTP 5xx.
- `UNKNOWN`: any response not covered by the exact contract.

Every successful normalized message carries a stable source locator:
`discord:guild:<guild>:channel:<channel>:message:<message>`.

Attachment URLs are intentionally omitted; only bounded attachment metadata is projected.

`externalEffectPerformed` is always false.

## Pagination and completeness

Discord explicitly documents that search can return fewer messages than the requested limit for old/unaccessed data, and clients must not use `messages.length` as a pagination-completeness signal. Discord also documents that `total_results` can be inaccurate while messages are actively created/deleted.

Therefore this provider always returns:

`provider.paginationComplete = false`

and treats provider totals as observations, not completeness authority.

A higher-level caller may request additional offsets, but no V0 response may claim a complete corpus merely because one page is short or `total_results` appears exhausted.

## Retry ownership

This workflow performs one provider attempt. It surfaces 202/429 retry facts instead of hiding them behind unbounded retries. Durable wait/retry belongs to the caller's workflow/process owner when needed.

## Scope enforcement

The request must always specify channel IDs. The authoritative ability to read those channels remains Discord's permission model for the installed Bot. `authorityRef` is recorded for provenance but does not itself grant access.

Qualification must include:
- known-positive allowed channel;
- out-of-scope or denied channel negative case;
- no-write-effect observation.

## Non-goals

Not in V0:
- user token/self-bot;
- historical mirror/collector;
- Gateway WebSocket daemon;
- attachment download;
- semantic/vector search;
- public knowledge publishing;
- model-training corpus;
- Discord-specific Gateway or MCP mega-service.

Open those only from concrete qualification counterexamples.
