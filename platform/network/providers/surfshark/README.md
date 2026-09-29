# Surfshark provider profile

This directory contains provider-specific material only. It is not part of generic Network graduation.

Current responsibilities:

- pinned `gluetun-servers` snapshot as reproducible endpoint/public-key catalog metadata;
- protected standard WireGuard client profiles under `/etc/network-v2/providers/`;
- reusable provider capability acceptance retained separately from production consumers;
- historical provider discovery/admission evidence under `history/`.

Private WireGuard credentials remain outside Git in root-owned files under `/etc/network-v2/providers/`. A protected WireGuard client identity is a **single-session physical authority**: the same client identity/address must not be instantiated concurrently by multiple consumers or by multiple provider endpoints. WireGuard roaming semantics let a peer move the authenticated client endpoint to the most recently observed UDP source, so duplicated sessions can steal the same provider identity from one another while every local process still appears healthy.

Current production therefore has one physical provider session in `nv2-browserless-prod`. `network-v2-browserless-provider-carrier.service` projects that session as an internal carrier only. Finance, Supply-Chain, Claude and ChatIngress retain their own destination/policy authorities and do not materialize provider credentials. A future genuinely concurrent physical carrier requires a distinct provider-issued WireGuard identity/key pair; copying the existing protected profile is not an admissible failover mechanism.

Cross-consumer recovery qualification on 2026-09-26 selected the current `th-bkk` catalog profile for the shared carrier because one serialized session carried OpenAI/ChatGPT network consequences, Anthropic, Docker/Google/Elastic registries, OKX and Binance in the same observation window. This is a current deployment choice, not a claim that one site is universally superior. Destination consequence remains separate from provider-carrier liveness.

The former live Gluetun updater + custom qualification lane was retired after consumer census showed that no current production authority consumed `latest.json` or `qualified-*.json`. Reusable WireGuard implementation/lifecycle support lives under `capabilities/wireguard/`; consumer destination/fail-closed policy belongs under `consumers/`.

OpenAI/ChatGPT reachability and Chromium navigation remain Browserless consumer acceptance. Finance venue semantics and OCI registry semantics remain their consumer owners.
