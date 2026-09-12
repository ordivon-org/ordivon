# Surfshark provider profile

This directory contains provider-specific material only. It is not part of generic Network graduation.

Current responsibilities:

- pinned Gluetun server catalog as public endpoint/server metadata authority;
- static sing-box carrier configuration for a provider namespace;
- provider carrier acceptance;
- historical provider discovery/admission evidence under `history/`.

Private WireGuard credentials remain outside Git in root-owned files under `/etc/network-v2/providers/`.

Reusable WireGuard implementation/lifecycle support lives under `capabilities/wireguard/`; consumer destination/fail-closed policy belongs under `consumers/`.
