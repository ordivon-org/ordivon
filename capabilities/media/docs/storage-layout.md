# Storage layout

The Studio repository contains no large media root. The local and remote layouts are external but deterministic.

## Windows working root

Recommended initial root:

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

The content-addressed cache mirrors remote object keys. Human working directories may use descriptive names. For a selected payload whose canonical bytes are **not already retained by Git or another owner-native durable store**, committing only its digest is insufficient: the exact bytes must cross a verified durable storage boundary before disposable production work is closed.

The minimum local write/read pair is:

```bash
uv run ordivon-studio archive <selected-media> --cache-root /mnt/d/OrdivonStudio/cache
uv run ordivon-studio materialize <sha256:digest> <working-path> --cache-root /mnt/d/OrdivonStudio/cache
```

`archive` hashes the source, derives the immutable object key, copies through a temporary file, verifies the copied bytes, and admits the object without overwriting an existing digest address. Repeating the same exact Blob converges to the existing verified object.

`materialize` performs the inverse working operation without changing the cache: it resolves the immutable object key from the requested digest, verifies the cached object **before** copying, copies through a temporary file, verifies the working copy, and admits it without overwriting different destination bytes. Repeating materialization to an exact existing destination converges. A missing or corrupt cache object fails closed.

This pair supplies local byte durability and recovery; it is not a media database or publication system. Git-tracked exact payloads do not need duplicate CAS storage merely because they also have a SHA-256 identity.

## R2 object keys

```text
objects/sha256/<first-two-hex>/<complete-sha256>
```

Semantic names remain in Git Asset manifests. The object key never contains a mutable title such as `final.mp4`.

## Upload behavior

- use copy, not destructive sync;
- reject a destination object that exists with different bytes;
- verify size and digest after transfer;
- do not expose the source bucket publicly;
- publish through a separate delivery path or copied public object;
- do not use R2 as the live Resolve media disk.

The transport is intentionally not fixed in this foundation. It may use `rclone` or another S3-compatible client after bucket, credentials, retention, and restore behavior are configured and tested. Asset and Blob identifiers do not depend on that choice.
