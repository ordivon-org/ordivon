# Surfshark provider profile

This directory contains provider-specific material only. It is not part of generic Network graduation.

Current responsibilities:

- pinned `gluetun-servers` snapshot as reproducible endpoint/public-key catalog metadata;
- protected standard WireGuard client profiles under `/etc/network-v2/providers/`;
- reusable provider capability acceptance retained separately from production consumers;
- historical provider discovery/admission evidence under `history/`.

Private WireGuard credentials remain outside Git in root-owned files under `/etc/network-v2/providers/`. Current Finance production composes those protected profiles with the pinned numeric catalog directly into sing-box WireGuard Endpoints. Browserless still consumes the materialized catalog profiles until its separate migration closes.

The former live Gluetun updater + custom qualification lane was retired after consumer census showed that no current production authority consumed `latest.json` or `qualified-*.json`. It duplicated transport consequence testing while depending on legacy Surfpath/ExteriorAnchor/Browserless quiescence. Provider-path health and failover are now established by the mature consumer data planes themselves (for Finance, sing-box WireGuard Endpoint + URLTest + real consequence acceptance).

Reusable WireGuard implementation/lifecycle support lives under `capabilities/wireguard/`; consumer destination/fail-closed policy belongs under `consumers/`.

OpenAI/ChatGPT reachability and Chromium navigation remain Browserless consumer acceptance, not Surfshark provider truth.
