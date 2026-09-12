# Surfshark provider profile

This directory contains provider-specific material only. It is not part of generic Network graduation.

Current responsibilities:

- pinned `gluetun-servers` snapshot as reproducible catalog/reference metadata;
- pinned Gluetun updater as live provider candidate-discovery authority; live output is explicitly partial and never grants tunnel authority;
- static sing-box carrier configuration for a provider namespace;
- provider carrier acceptance;
- historical provider discovery/admission evidence under `history/`.

Private WireGuard credentials remain outside Git in root-owned files under `/etc/network-v2/providers/`.

Reusable WireGuard implementation/lifecycle support lives under `capabilities/wireguard/`; consumer destination/fail-closed policy belongs under `consumers/`.

## Live candidate discovery

`live/discover.sh` runs the exact pinned Gluetun updater against Surfshark's current provider API. In the 2026-09-12 acceptance observation, Gluetun's default `minratio=0.8` failed closed because the provider returned fewer servers than its embedded completeness expectation. Network v2 therefore uses a separately declared `minratio=0.5` only for **candidate discovery**, records `completenessClaim=false`, and requires every candidate used for execution to pass a separate cryptographic transport and destination-consequence gate. A fresh partial snapshot is not a provider catalog completeness claim and is not execution authority.

`live/qualify-wireguard.sh` is the separate effectful gate. Because current production and Network v2 share the same Surfshark WireGuard client identity, qualification runs under the existing Surfpath graduation lease, quiesces the exact legacy generation, tries only endpoints named by one fresh live snapshot, requires a real WireGuard handshake plus namespace DNS, generic HTTPS and public-egress consequences, writes a time-bounded qualification receipt, and then restores production after releasing the lease.

OpenAI/ChatGPT reachability and Chromium navigation remain Browserless consumer acceptance, not Surfshark provider truth.
