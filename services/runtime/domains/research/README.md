# Research Domain

`domains/research/` owns business-level analysis semantics.

This package is for:

- analysis requests and analysis results
- analysis persistence objects that still belong to research meaning
- services that manage analysis lifecycle as a business artifact

This package is not for:

- prompt text
- workflow routing
- final risk policy enforcement
- generic operational counters

Default rule:

If the object answers "what did we analyze and what did we conclude?", it likely belongs here.
