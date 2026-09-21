output "browserless_human_public_origins" {
  description = "Harness-compatible public origin map. No credential material is included."
  value = {
    for _, handoff in local.handoffs :
    handoff.endpoint_id => "https://${handoff.hostname}"
  }
}

output "handoff_hostnames" {
  description = "Cloudflare Access protected handoff hostnames."
  value       = sort(tolist(local.handoff_hostnames))
}

output "gateway_mcp_hostname" {
  description = "Stable Cloudflare Access protected Gateway MCP hostname."
  value       = local.gateway.hostname
}

output "gateway_mcp_audience" {
  description = "Non-secret Access application audience required by the Gateway origin verifier."
  value       = cloudflare_zero_trust_access_application.gateway_mcp.aud
}
