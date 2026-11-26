# Media R13 — selected toolchain and native validation discovery

Host #32756, extending R11/R12. Existing 13 responsibility domains remain:
L01 intent, L02 source/claims, L03 visual grammar, L04 asset/rights,
L05 state/impact, L06 editorial, L07 timed text, L08 equipment,
L09 native processing, L10 perception, L11 quality, L12 delivery,
L13 research. Scope here L08/L09/L11/L12, not a new registry.
Mature carriers: mise/uv, Python unittest, FFmpeg/FFprobe, OTIO, ttconv;
Core Python and provider-specific Python remain distinct.

## P0 selected toolchain

Use [uv Python selection](https://docs.astral.sh/uv/concepts/python-versions/),
[uv resolution](https://docs.astral.sh/uv/concepts/resolution/) and
[mise version requests](https://mise.jdx.dev/dev-tools/versions.html).
I owner manifests and eligible release; O compatible language range,
exact selected interpreter, native lock and materialization receipt.
S Git and existing owner-local environment. pre selected version available;
native resolver and frozen install succeed. post selected interpreter,
locked packages and receipt agree. inv compatibility != exact execution;
old historical receipts stay immutable; no global owner mutation.
eff local source and disposable environment only. c one native resolution
and materialization. epsilon no production identity claim. prov exact
versions/lock/materialization/readback. unfold select -> resolve -> install ->
observe -> qualify. Python 3.15.2 / uv 0.13.10 candidate PR #2825.

## P1 complete native gate

Use [unittest discovery](https://docs.python.org/3/library/unittest.html#test-discovery).
I exact source cut, provider-compatible OTIO Python 3.13 environment and
existing native binaries. O four smoke outcomes and one discovered native
Python suite. S disposable per-attempt fixtures and existing provider env.
pre owner toolchain available, optional provider tests intentionally invoked.
post every discoverable test*.py under processing/tests executes in the
explicit native gate. inv no nested discovery in a smoke script; no
hand-maintained filename enumeration in the full gate; lightweight core
does not materialize optional native providers. Keep shell smoke commands
individually usable. eff read source, create disposable fixtures. c one
provider test environment activation; discovery proportional to test modules;
no latency claim without a matched benchmark. epsilon test discovery is not
proof of coverage of all conceivable behaviors. prov actual native suite and
a temporary failing discoverable sentinel (never committed).
unfold check:all -> check + processing:check -> four named smoke commands +
processing:test -> native unittest discovery -> independent actual outcomes.
Python 3.13 is for OTIO wheel compatibility, not Core selection.
No speculative dependency or bespoke runner.

P0 normal merge queue and real consumers: restore exact original master/narration
only via scoped binding; Web token second consumer remains unverified (#32687).
P1 dependency updates through eligible versions and normal CI; preserve supply-chain
policy and provider compatibility. P2 actual bottleneck measurements before
algorithm changes. No actual publication or human acceptance implied.
