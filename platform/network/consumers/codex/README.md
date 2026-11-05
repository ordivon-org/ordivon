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
