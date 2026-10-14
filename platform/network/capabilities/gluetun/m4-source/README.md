# M4 — Native owned lifecycle source candidate (nonproduction)

This is a real systemd/Podman Quadlet source prototype for the already
qualified Gluetun mechanism. It is not installed, enabled or authorized
to interrupt the current legacy Surfshark session.

The M3B real production canary succeeded and restored Legacy by design.
The remaining M4 question is **who owns sustained service lifecycle and
independent recovery when the initiating shell exits or crashes**.

Composition:
- `network-v2-gluetun-owned.network`: isolated /30 Podman-owned native network;
- `network-v2-gluetun-owned.container`: pinned Gluetun image, exact veth port,
  native systemd failure hook, no automatic physical reconnect;
- `network-v2-gluetun-owned-adapter.service`: existing candidate sing-box
  config, original consumer seam and namespace, BindsTo candidate service;
- `network-v2-gluetun-legacy-restore.service`: native manager failure hook;
- `m4-owned-restore-legacy`: guarded candidate-absent-before-legacy core restore.

Safety / status:
- No [Install] section, no materialization, no new Provider identity and no
  effect on the current production services.
- The owned-mode admission marker and two negative WG checks prevent
  ordinary accidentally concurrent physical sessions; they are not security
  controls against a privileged Podman administrator or changing the marker
  behind a running service.
- No `Restart=always` or `Restart=on-failure`: silently reconnecting a
  failed candidate concurrently with fallback could reuse Surfshark's sole
  physical identity.
- A source-only, exact-scoped activation/maintenance transaction is STILL
  required. Its admission marker is not itself authorization.
- This recovery helper restores only WG/DNS/carrier/target after verifying
  candidate absence. It does **not** prove producer/consumer readiness or
  an exact full-platform recovery. That is the next nonproduction M4
  acceptance frontier, not a claim of completion.
- Before permanent mode: test manager-triggered candidate failure,
  initiator SIGKILL, consumer readiness, machine reboot, mode fencing,
  unit generator/Stop/OnFailure behavior, rollback freshness and
  rootful Podman admin trust boundary. Then separately approve M4
  ownership. Never auto-retire Legacy because M3B succeeded.

## Explicit provider-mode composition

M4 does not add Gluetun to the already enabled legacy Browserless target.
The staged replacement network-v2-browserless.target owns only the retained
netns/veth substrate. Provider realization is selected by exactly one mode:
network-v2-gluetun-owned.target for Gluetun or
network-v2-browserless-legacy-provider.target for fallback. The owned target
is staged, not installed or enabled by ordinary legacy materialization.

Consumer services do not own provider lifecycle. They may keep running while
the carrier is absent and fail closed at the HTTP seam. Manager-owned fallback
removes the owned admission marker, positively proves the Gluetun container
absent, switches boot selection to the legacy provider target, then verifies
the legacy core and installed consequence probes.

## Nonproduction lifecycle evidence

Two effectful-but-nonproduction acceptance commands are deliberately kept
outside the ordinary all:validate path:

- task capability:gluetun:m4:systemd-manager-sandbox creates uniquely named
  temporary units under /run/systemd/system, kills the disposable initiator,
  then proves PID 1 still observes candidate exit/SIGKILL and invokes OnFailure
  recovery in candidate-absent -> legacy -> consumer -> producer order. It
  removes every sandbox unit before PASS and never uses provider credentials.
- task capability:gluetun:m4:browserless-proxy-sandbox runs the pinned real
  Browserless Chromium image on a Podman internal network. The synthetic
  target is reachable only when Chromium receives the provider proxy launch
  argument; the otherwise identical direct launch fails closed.

These prove service-manager ownership and browser proxy composition without
using the sole production Surfshark identity. They do not simulate a machine
power loss or authorize permanent M4 ownership.

## Durable boot mode

Permanent owned-provider selection uses the root-controlled marker
/etc/network-v2/gluetun/m4-owned-mode.selected. It is intentionally separate
from temporary runtime state: reboot clears /run but must not silently erase
a previously adopted provider mode. No validation/materialization task creates
this marker. Fallback clears it only after the Gluetun candidate is positively
absent, then disables owned mode and enables/starts the Legacy provider target.
