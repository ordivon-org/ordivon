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

output "gateway_windows_access_service_token_id" {
  description = "Non-secret service-token identity used to bind the canary Windows Runtime Service Auth policy."
  value       = cloudflare_zero_trust_access_service_token.gateway_windows_runtime.id
}

output "gateway_windows_access_client_id" {
  description = "Sensitive Gateway machine-identity client ID. Materialized only by the fixed Cloudflare owner."
  value       = cloudflare_zero_trust_access_service_token.gateway_windows_runtime.client_id
  sensitive   = true
}

output "gateway_windows_access_client_secret" {
  description = "Sensitive Gateway machine-identity client secret. Materialized only by the fixed Cloudflare owner."
  value       = cloudflare_zero_trust_access_service_token.gateway_windows_runtime.client_secret
  sensitive   = true
}
