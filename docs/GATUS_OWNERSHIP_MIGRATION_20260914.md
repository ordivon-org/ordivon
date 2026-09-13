# Gatus ownership migration

Date: 2026-09-14

Status: **OPERATIONS DEPLOYMENT OWNER / UPSTREAM GATUS IMPLEMENTATION**

The live Gatus service was already recognized by Operations as the mature black-box monitoring substrate, but its desired-state files and deploy script still lived in `/root/workstation-lab`. This migration removes that ownership contradiction. Operations now owns only the local deployment lifecycle and monitoring configuration under `observability/gatus/`; Gatus remains the upstream implementation and observed domains remain their own semantic authorities.

The reviewed binary admission is preserved unchanged: Gatus 5.36.0, exact binary SHA-256, upstream Go module identity, reviewed OCI digest and source revision. Deployment never downloads an unreviewed binary implicitly.

The Operations-owned config also adds four bounded direct-profile black-box observations: Cloudflare trace and GitHub through the existing loopback CONNECT carriers on ports 19081 and 19082. These checks replace the corresponding bespoke `netcontinuity` target probes. They prove only point-in-time reachability through the selected local carrier. They do not establish Finance acceptance, Windows-native serviceability, provider catalog truth, or future availability.

Cloudflared connector HA metrics remain provider-native metrics and should be scraped/observed through standard telemetry rather than reimplemented in another custom continuity daemon. Source/route convergence remains owned by the existing Cloudflare/direct-route lifecycle.
