# Codex: Network-owned scoped egress

The consumer reuses ONE existing Network-v2 Gluetun/WireGuard physical provider.
It is not a second VPN and does not manage the Surfshark Windows GUI.

Linux scoped Codex transport is available at 127.0.0.1:19982, but that
is not the ordinary Windows Desktop startup path. The Windows interactive
user instead uses its native system proxy at 127.0.0.1:19781, with the
upstream Codex respect_system_proxy feature enabled in user config.
Windows policy and boot persistence are owned by Workstation; Network
owns the downstream shared carrier, scoped relay and proof obligations.
The scoped Network relay forwards from host 127.0.0.1:19982 to namespace
127.0.0.1:19980; the sing-box policy forwards admitted HTTPS destinations
to the shared provider 10.252.246.2:19680. Its last rule rejects all
unknown destinations, with no direct route or second client WireGuard identity.

These files were imported from the deployed /etc/network-v2 and
/etc/systemd/system and /usr/local/libexec/network-v2 paths on 2026-11-05,
because the corresponding consumer SourceCut was absent from the inspected Git
snapshot. Importing the source does not by itself redeploy the live services.

The native ready.sh gate checks actual ChatGPT HTTPS consequence and negative
rejection of an unrelated public domain. Windows Desktop, CLI, OAuth and
MCP request-path acceptance remains a separate consumer task: an application
profile change requires a process restart and real request observations.

## Observed Windows Codex application boundary — 2026-11-05

The scoped policy includes exactly `persistent.oaistatic.com`, a Codex
desktop CDN dependency observed by the native `codex doctor --json` check.
The shared physical provider reached this host with CONNECT=200, TLS complete
and origin HTTP 404 on the root path, while the old narrower Codex policy
returned CONNECT=200 but an incomplete TLS handshake. The source now tests
actual ChatGPT and CDN HTTPS transport and retains explicit unknown-domain
denial. Origin HTTP 404 for the CDN root is accepted **only as transport**
evidence; no application asset download is claimed.

On Windows, a fresh Codex CLI reads `$HOME/.codex/.env` at process startup.
A fresh 0.166.0-alpha.6 diagnostic recognized the configured Network proxy
variables, but the existing ChatGPT-hosted Codex processes started *before*
that dotenv was changed. This readiness witness therefore emits
`applicationProcessEgress: UNKNOWN` rather than asserting that already-running
Windows processes use the scoped proxy. A true process-restart and a trace
of its actual requests is a separate consumer acceptance obligation.


## Windows process-level observation (DEV-01)

Use the mature upstream psutil library for a read-only snapshot of already
running Windows desktop and Codex processes:

    uv run --no-project --with 'psutil>=7,<8' python consumers/codex/windows_process_egress.py

The **default proxy port is now 19781**, matching the Windows Desktop
system-proxy/shared-egress path. Port 19982 is the *distinct Linux scoped*
Codex transport and can be explicitly selected with `--proxy-port 19982`.
The older 19982 default silently missed the two real Session 1 Codex TCP
connections observed on Windows at 127.0.0.1:19781.

This source-owned one-shot LEGO reports only names/PIDs, HTTP(S) proxy
environment binding classification, whether a process predates the .codex/.env
file and aggregated local-proxy versus nonlocal TLS socket counts.
A local-proxy TCP socket is now reported **even when proxy environment is
UNSET or UNREADABLE**: Windows Desktop commonly uses a system-proxy
setting rather than HTTP_PROXY/HTTPS_PROXY. When both proxy and external
TCP/443 sockets exist, the observation reports both without inventing
which application request used either one. It never
prints proxy values, credentials, remote addresses or command lines. Unreadable
processes are UNKNOWN, not empty. Its standing is always
END_TO_END_EGRESS_UNKNOWN: a scoped environment and even an observed proxy TCP
socket alone cannot certify Codex API traffic or Gluetun upstream forwarding.
Pair the result with the existing NS2 upstream spy and a fresh actual client
request before any process-level route claim.

## Windows normal application startup and evidence (2026-11-07)

The former PowerShell per-process launcher was superseded by normal Desktop
launch with the upstream Windows system proxy; it never configured the Desktop
itself and has no remaining supported consumer.

- The interactive Windows system proxy targets Ordivon's 127.0.0.1:19781
  public-web VPN proxy. Native Codex respect_system_proxy is enabled.
- The separate 127.0.0.1:19982 Linux Codex consumer remains scoped to
  admitted ChatGPT destinations and rejects unknown origins.
- The Windows Chrome app has its own native fixed_servers policy; it is not
  configured through the former Codex launcher.
- Check actual application sockets plus a real HTTPS request. A bounded
  local-proxy TCP observation does not certify universal DNS/UDP/QUIC routes.

Do not recreate a manual CLI wrapper, second physical WireGuard identity,
or Network-owned Windows system-proxy manager.
