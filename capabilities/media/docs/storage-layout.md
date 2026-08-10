# Storage layout

The Studio repository contains no large media root. Working paths and byte replicas are external, while semantic identity remains in Git.

## Windows working root

```text
D:\OrdivonStudio\
├── cache\objects\sha256\
├── productions\runtime-introduction\
│   ├── capture\
│   ├── audio\
│   ├── resolve\
│   ├── proxies\
│   └── review\
└── exports\
```

For a selected payload whose canonical bytes are **not already retained by Git or another owner-native durable store**, committing only its digest is insufficient. The exact bytes need a recoverable durable authority appropriate to the medium.

## Local content-addressed durability

The local write/read pair is:

```bash
uv run ordivon-studio archive <selected-media> --cache-root /mnt/d/OrdivonStudio/cache
uv run ordivon-studio materialize <sha256:digest> <working-path> --cache-root /mnt/d/OrdivonStudio/cache
```

`archive` hashes the source, derives the immutable object key, copies through a temporary file, verifies the copied bytes, and admits the object without overwriting an existing digest address. Repeating the same exact Blob converges.

`materialize` verifies the cached object before copying, verifies the working copy, and never overwrites different destination bytes. A missing or corrupt cache object fails closed.

This is sufficient for Workspace/process loss. It is **not** sufficient to claim tolerance of loss of the workstation or its D: volume.

## Independent R2 replica

P4 accepted one real off-machine replica using the existing private Cloudflare R2 bucket `ordivon-artifacts` and the Cloudflare Account Object API. The bucket's managed `r2.dev` domain was disabled and it had no custom domains during acceptance.

The provider-specific commands are intentionally narrow:

```bash
uv run ordivon-studio r2 replicate <local-blob> \
  --bucket ordivon-artifacts \
  --credentials <operator-secret-json>

uv run ordivon-studio r2 restore <sha256:digest> \
  --cache-root /mnt/d/OrdivonStudio/cache \
  --bucket ordivon-artifacts \
  --credentials <operator-secret-json>
```

The credential JSON remains outside Git and supplies `account_id` and `api_token`. Studio never writes those values into a Production Receipt.

`r2 replicate`:

1. derives `objects/sha256/<first-two-hex>/<complete-sha256>`;
2. GETs an existing remote key first;
3. if it exists, downloads and SHA-256 verifies the actual bytes before converging;
4. if absent, PUTs the local bytes;
5. redownloads the new object and verifies exact size and SHA-256 before reporting success.

`r2 restore` downloads the remote digest key to a temporary local file, verifies SHA-256, then admits it into the local CAS without overwriting divergent local bytes. The restored CAS object can then be passed through ordinary `materialize`.

### Current write-semantics boundary

The Cloudflare Account Object API path exercised in P4 did **not** enforce `If-None-Match: *` on PUT: a probe against an existing exact object returned HTTP 200 rather than a create-only precondition failure. Therefore the current adapter is explicitly **single-writer**:

```text
GET/preflight
→ optional PUT
→ mandatory GET + SHA-256 verification
```

It does not claim atomic multi-writer no-overwrite admission. If concurrent independent writers become real, use a provider path with proven conditional creation or add a separate owner-level serialization mechanism; do not widen this adapter by assumption.

## P4 destructive-loss acceptance

Runtime Introduction supplied the real failure test. Its picture master was replicated and independently redownload-verified in R2. The local CAS object was then quarantined; ordinary local `materialize` failed because the object was genuinely absent. `ordivon-studio r2 restore` reconstructed the CAS object only from R2, exact SHA-256 was re-established, and the restored working MP4 retained its 78-second 1920×1080/30fps H.264 BT.709 structure.

The selected picture master, narration stem, and final English A/V candidate are all now present as verified R2 replicas. See `productions/runtime-introduction/evidence/r2-replica.receipt.json`.

## Object keys

```text
objects/sha256/<first-two-hex>/<complete-sha256>
```

Semantic names remain in Git Asset/Production records. Remote keys do not contain mutable names such as `final.mp4`.

## Boundaries

- use copy/replication semantics, never destructive sync as the authority model;
- verify actual downloaded bytes rather than trusting filenames or ETags as SHA-256;
- keep source buckets private; publication uses a separate delivery surface;
- do not mount R2 as the live Resolve media disk;
- do not duplicate exact Git-owned text/code payloads into media CAS merely for uniformity;
- one proven remote backend does not justify a generic multi-cloud storage framework.
