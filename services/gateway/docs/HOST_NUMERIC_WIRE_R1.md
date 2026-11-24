# Host V1 exact numeric wire projection

Host source PR #2624 is the natural Owner contract: nonnegative exact JSON
coordinates up to 2^53-1; Work revisions start at one and new CAS inputs leave
room for their successor. Gateway previously accepted coercible float/string
values for some Host coordinates and old BIGINT revision limits. A downstream
Host cannot recover an input already coerced by its adapter.

Use native Pydantic strict bounded types in the nine corresponding public tools.
No duplicate digest implementation or Host DB import. The original broad
snapshot and list ABI is retained. Native SDK invalid numeric inputs may now
be rejected before the adapter's legacy Owner-error envelope; valid inputs
are forwarded unchanged. Package 0.10.21, epoch 18 records the deliberate
input-schema change; existing valid request payloads remain unchanged.

The native SDK test exercises the real Gateway server against an observing
Owner port: both endpoints are forwarded exactly and invalid inputs never reach
the port. This is source-bound evidence, not an installed Gateway or independent
Security admission witness. Production cutover still needs #2349 and separate
actual Host candidate compatibility/readback. Host output sequence exhaustion
and message.search pagination typing are separate obligations.
