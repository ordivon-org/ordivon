# Gatus ownership migration

Date: 2026-09-14

Status: **OPERATIONS DEPLOYMENT OWNER / UPSTREAM GATUS IMPLEMENTATION**

The live Gatus service was already recognized by Operations as the mature black-box monitoring substrate, but its desired-state files and deploy script still lived in `/root/workstation-lab`. This migration removes that ownership contradiction. Operations now owns only the local deployment lifecycle and monitoring configuration under `observability/gatus/`; Gatus remains the upstream implementation and observed domains remain their own semantic authorities.

The reviewed binary admission is preserved unchanged: Gatus 5.36.0, exact binary SHA-256, upstream Go module identity, reviewed OCI digest and source revision. Deployment never downloads an unreviewed binary implicitly.

The Operations-owned config originally carried four bounded `native-a/native-b` black-box observations as a migration bridge from bespoke `netcontinuity`. Those checks were retired rather than preserving legacy carriers for monitoring. A follow-up attempt to point Gatus at Network v2 CONNECT authorities was also removed: the reviewed Gatus Go client repeatedly observed connection resets while the canonical Network v2 consequence clients returned HTTP 200 at the same time. Operations therefore does not maintain a second transport-health client or compatibility shim. Network v2/sing-box owns provider health and failover; its destructive acceptance owns transport consequence proof, while Gatus continues to monitor ordinary service/API consequences that it can observe natively.

Cloudflared connector HA metrics remain provider-native metrics. Operations Prometheus now scrapes the production A/B metric endpoints on ports 20243/20244, preserving the raw `cloudflared_tunnel_ha_connections` time series without reimplementing a continuity verdict. Source/route convergence remains owned by the existing Cloudflare/direct-route lifecycle.
