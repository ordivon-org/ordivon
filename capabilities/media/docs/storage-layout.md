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

The content-addressed cache mirrors remote object keys. Human working directories may use descriptive names, but selected assets are not durable merely because their digest appears in `assets.json`: the selected bytes must also be copied into a verified content-addressed store before disposable production work is closed.

The minimum local gate is:

```bash
uv run ordivon-studio archive <selected-media> --cache-root /mnt/d/OrdivonStudio/cache
```

`archive` hashes the source, derives the immutable object key, copies through a temporary file, verifies the copied bytes, and admits the object without overwriting an existing digest address. Repeating the same exact Blob converges to the existing verified object. This is local byte durability, not a media database or publication system.

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
