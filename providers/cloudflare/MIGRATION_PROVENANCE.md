# Migration provenance

This provider repository was physically extracted on 2026-09-13 from:

- source repository: `/root/projects/ordivon-world`
- source revision: `4f908b237d45a8e8759bfdf3ec41dab8e4b73948`
- source subtree: `providers/cloudflare/`

The extraction changes physical ownership only. Remote Cloudflare deployment state, R2 state, request/receipt identities, client secrets, and historical receipts are not rewritten by this operation.

The former World repository remains immutable provenance for pre-extraction history.

## Operations absorption — 2026-09-13

The short-lived standalone provider repository at `/root/projects/ordivon-cloudflare-provider` was an extraction/cutover staging point only. Its final staging revision was `44f0cc3eb19e665f61b942bf24915ea06c493eb2`. The maintained source is now `/root/projects/ordivon-workstation-v2/providers/cloudflare` under `ordivon-workstation-v2`.

Operations owns source maintenance, installation, local service/timer realization, and operational health/SLO plumbing. Cloudflare/provider-native systems retain authority for Worker/R2/request/receipt state; consuming domains retain task meaning, authorization, and semantic verification.
