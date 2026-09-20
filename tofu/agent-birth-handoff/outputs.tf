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
