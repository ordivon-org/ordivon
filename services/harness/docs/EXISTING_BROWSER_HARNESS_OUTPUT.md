# Existing Windows Browser Harness result observation

The operator-local candidate `scripts/existing_browser_harness_output.py` reuses
the shared exact DOM output qualifier via the already authorized Browser Harness
daemon. It is qualified against Browser Harness 0.1.13; the natural Workstation
owner must bind the exact daemon name, IPC directory and interpreter. Do not
expose an arbitrary daemon name or target as a public domain authorization.

The caller supplies the durable expected prompt digest, canonical provider
resource and a fresh observation ID (reuse that ID only to recover the same
observation). An exact UTF-8 prompt file is optional corroboration; the reader
matches observed user-message UTF-8 bytes to the digest without transporting
the original prompt or re-normalizing the observed bytes. The reader enumerates exact targets,
attaches a temporary explicit CDP session, evaluates the fixed observation
expression, verifies the target set again and detaches only its own session.
It does not change the daemon's shared current tab or auto-start Chrome.
SDK or attachment ambiguity, unavailable sessions and nonqualified output are
reported without unrelated DOM text. Only the selected assistant output is
delivered on CAPTURED. No CLI telemetry wrapper is used.

CAPTURED denotes an observed role pair, not a provider-issued Turn ID, durable
SEND success, recipient acceptance or permission to release a carrier.
This primitive does not restore the retired public MCP result or release APIs.
Native isolated qualification is not proof of a live approved account or
production consumer. Production use still requires effect identity binding,
authenticated consumer and the normal release gate.

## Optional forward-only DOM corroboration

The existing Playwright SEND receipt may carry an optional `observedUserAppendWitness`. It requires one newly appended visible user
message with an exact prompt digest and unchanged ordered earlier user identities
before and after the already-authorized SEND. Missing, duplicate, reordered or
changed identities yield no witness; the existing SEND standing is unchanged.
Only a derived digest of the earlier identity list is persisted, not its text.

A caller may pass the exact DOM user-message identity from that verified receipt
to either read primitive via `--expected-dom-user-message-id`. This requires
the matching unique visible user identity and exact prompt digest/text; it
does not substitute a historical same-text user message. It remains an
OBSERVED_DOM_MESSAGE_ID_MATCH, not proof of provider-issued identity, exclusive
causality, a new SEND, recipient acceptance, or carrier release eligibility.
Old receipts cannot be retroactively upgraded. The unanchored result remains
OBSERVED_ROLE_PAIR_ONLY. The authorization boundary is the existing natural
consumer, not arbitrary values supplied to a command line.
