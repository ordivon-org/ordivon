# Codex: Network-owned scoped egress

The consumer reuses ONE existing Network-v2 Gluetun/WireGuard physical provider.
It is not a second VPN and does not manage the Surfshark Windows GUI.

Windows Codex opts in through its per-application .codex/.env, pointing HTTP(S)
proxy variables at 127.0.0.1:19982. Windows global proxy settings remain unchanged.
The Network relay forwards from host 127.0.0.1:19982 to namespace
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
