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

The content-addressed cache mirrors remote object keys. Human working directories may use descriptive names, but selected assets are registered by digest before archival.

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
