# Surfshark — provider metadata and explicit recovery profile

**Current physical owner:** `providers/gluetun/`. The selected production
provider is **one** Gluetun Quadlet with native `VPN_SERVICE_PROVIDER=surfshark`,
WireGuard credentials provided through a Podman Secret, and a country-restricted
native Gluetun server selector (`Singapore,Japan`). See
`providers/gluetun/README.md` for the SourceCut and real consumer acceptance.

This directory owns only the Surfshark-specific **legacy recovery input**
and a reusable provider-carrier acceptance gate:

- `config/carrier.json` and `acceptance/carrier-smoke.sh` validate a carrier
  already owned by Network. They never create another WireGuard identity.
- `external/gluetun-servers.lock` and the `catalog`, `profiles`, `verify-local`
  Taskfile tasks support the inactive, explicitly invoked, serialized
  Browserless/WireGuard fallback. They must not run concurrently with Gluetun.
- Protected static WireGuard profile inputs under `/etc/network-v2/providers/`
  are recovery inputs, **not** the currently selected endpoint or secret owner.

These fallback tasks are retained because
`consumers/browserless/production-cutover.sh` can consume the generated
profile manifest during explicit disaster recovery. They are **not** the
normal server rotation mechanism; that belongs to Gluetun's native updater,
healthcheck and server selector.

The old R1/R2 discovery reports were unreferenced by current consumers and
removed from the working tree. Their content remains recoverable from Git
history if an investigation actually requires it. No Network application
consumer may instantiate the shared provider WireGuard private key in a
second simultaneous session. Finance, Claude, Supply Chain and Codex own
their own destination policies but share the one admitted carrier.
