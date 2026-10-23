locals {
  handoffs = {
    "11" = {
      endpoint_id = "chatgpt-carrier-11"
      hostname    = "handoff-11.ordivon.com"
      service     = "http://127.0.0.1:16011"
    }
    "12" = {
      endpoint_id = "chatgpt-carrier-12"
      hostname    = "handoff-12.ordivon.com"
      service     = "http://127.0.0.1:16012"
    }
    "13" = {
      endpoint_id = "chatgpt-carrier-13"
      hostname    = "handoff-13.ordivon.com"
      service     = "http://127.0.0.1:16013"
    }
  }

  gateway = {
    hostname = "gateway-mcp.ordivon.com"
    service  = "http://127.0.0.1:8899"
  }

  handoff_hostnames = toset([
    for handoff in values(local.handoffs) : handoff.hostname
  ])
  managed_hostnames = setunion(
    local.handoff_hostnames,
    toset([local.gateway.hostname]),
  )
}

data "cloudflare_zero_trust_tunnel_cloudflareds" "production" {
  account_id = var.account_id
  name       = "ordivon-wsl"
  status     = "healthy"
  is_deleted = false
  max_items  = 2
}

check "one_healthy_production_tunnel" {
  assert {
    condition     = length(data.cloudflare_zero_trust_tunnel_cloudflareds.production.result) == 1
    error_message = "Expected exactly one healthy remotely managed ordivon-wsl tunnel."
  }
}

locals {
  production_tunnel_id = one([
    for tunnel in data.cloudflare_zero_trust_tunnel_cloudflareds.production.result : tunnel.id
  ])
}

data "cloudflare_zero_trust_tunnel_cloudflared_config" "production" {
  account_id = var.account_id
  tunnel_id  = local.production_tunnel_id
}

# Native Windows-owned Cloudflare carrier. It remains separate from the Linux
# production tunnel so WSL loss cannot remove the Windows Gateway ingress.
data "cloudflare_zero_trust_tunnel_cloudflareds" "native" {
  account_id = var.account_id
  name       = "ordivon-native-canary"
  status     = "healthy"
  is_deleted = false
  max_items  = 2
}

check "one_healthy_native_tunnel" {
  assert {
    condition     = length(data.cloudflare_zero_trust_tunnel_cloudflareds.native.result) == 1
    error_message = "Expected exactly one healthy remotely managed ordivon-native-canary tunnel."
  }
}

locals {
  native_tunnel_id = one([
    for tunnel in data.cloudflare_zero_trust_tunnel_cloudflareds.native.result : tunnel.id
  ])
}

data "cloudflare_zero_trust_tunnel_cloudflared_config" "native" {
  account_id = var.account_id
  tunnel_id  = local.native_tunnel_id
}

data "cloudflare_zero_trust_access_applications" "owner_template" {
  account_id = var.account_id
  domain     = "skills-mcp.ordivon.com"
  exact      = true
  max_items  = 2
}

check "one_owner_template_application" {
  assert {
    condition     = length(data.cloudflare_zero_trust_access_applications.owner_template.result) == 1
    error_message = "Expected exactly one skills-mcp.ordivon.com Access application."
  }
}

data "cloudflare_zones" "production" {
  account = {
    id = var.account_id
  }
  name      = "ordivon.com"
  status    = "active"
  max_items = 2
}

check "one_active_production_zone" {
  assert {
    condition     = length(data.cloudflare_zones.production.result) == 1
    error_message = "Expected exactly one active ordivon.com zone in the provider account."
  }
}

locals {
  owner_template_policies = one([
    for app in data.cloudflare_zero_trust_access_applications.owner_template.result : app.policies
  ])
  owner_template_allowed_idps = one([
    for app in data.cloudflare_zero_trust_access_applications.owner_template.result : app.allowed_idps
  ])
  owner_template_auto_redirect = one([
    for app in data.cloudflare_zero_trust_access_applications.owner_template.result : app.auto_redirect_to_identity
  ])
  owner_template_session_duration = one([
    for app in data.cloudflare_zero_trust_access_applications.owner_template.result : app.session_duration
  ])
  owner_template_enable_binding_cookie = one([
    for app in data.cloudflare_zero_trust_access_applications.owner_template.result : app.enable_binding_cookie
  ])
  owner_template_http_only_cookie_attribute = one([
    for app in data.cloudflare_zero_trust_access_applications.owner_template.result : app.http_only_cookie_attribute
  ])
  production_zone_id = one([
    for zone in data.cloudflare_zones.production.result : zone.id
  ])

  owner_email_candidates = distinct(flatten([
    for policy in local.owner_template_policies : [
      for include_rule in policy.include :
      try(include_rule.email.email, "")
      if try(include_rule.email.email, "") != ""
    ]
    if policy.decision == "allow"
  ]))

  current_ingress        = data.cloudflare_zero_trust_tunnel_cloudflared_config.production.config.ingress
  native_current_ingress = data.cloudflare_zero_trust_tunnel_cloudflared_config.native.config.ingress

  unmanaged_ingress = [
    for rule in local.current_ingress : rule
    if try(rule.hostname, null) != null && !contains(local.managed_hostnames, rule.hostname)
  ]

  catch_all_ingress = [
    for rule in local.current_ingress : rule
    if try(rule.hostname, null) == null
  ]

  # Preserve every existing named native ingress except the Gateway hostname we own,
  # then add the Windows Gateway route immediately before the unchanged catch-all.
  native_unmanaged_ingress = [
    for rule in local.native_current_ingress : rule
    if try(rule.hostname, null) != null && rule.hostname != local.gateway.hostname
  ]

  native_catch_all_ingress = [
    for rule in local.native_current_ingress : rule
    if try(rule.hostname, null) == null
  ]
}

check "one_owner_email_identity" {
  assert {
    condition     = length(local.owner_email_candidates) == 1
    error_message = "Owner template must expose exactly one email allow identity."
  }
}

check "one_tunnel_catch_all" {
  assert {
    condition = (
      length(local.catch_all_ingress) == 1 &&
      startswith(local.catch_all_ingress[0].service, "http_status:")
    )
    error_message = "Production tunnel must retain exactly one HTTP status catch-all ingress."
  }
}

check "one_native_tunnel_catch_all" {
  assert {
    condition = (
      length(local.native_catch_all_ingress) == 1 &&
      startswith(local.native_catch_all_ingress[0].service, "http_status:")
    )
    error_message = "Native tunnel must retain exactly one HTTP status catch-all ingress."
  }
}

resource "cloudflare_zero_trust_access_application" "handoff" {
  for_each = local.handoffs

  account_id                 = var.account_id
  name                       = "Ordivon Agent Birth Handoff ${each.key}"
  domain                     = each.value.hostname
  type                       = "self_hosted"
  session_duration           = "15m"
  app_launcher_visible       = false
  auto_redirect_to_identity  = local.owner_template_auto_redirect
  allowed_idps               = toset(local.owner_template_allowed_idps)
  enable_binding_cookie      = true
  http_only_cookie_attribute = true

  policies = [
    {
      name       = "Allow owner"
      decision   = "allow"
      precedence = 1
      include = [
        {
          email = {
            email = one(local.owner_email_candidates)
          }
        }
      ]
    }
  ]
}

resource "cloudflare_zero_trust_access_application" "gateway_mcp" {
  account_id                 = var.account_id
  name                       = "Ordivon Gateway MCP"
  domain                     = local.gateway.hostname
  type                       = "self_hosted"
  session_duration           = local.owner_template_session_duration
  app_launcher_visible       = false
  auto_redirect_to_identity  = local.owner_template_auto_redirect
  allowed_idps               = toset(local.owner_template_allowed_idps)
  enable_binding_cookie      = local.owner_template_enable_binding_cookie
  http_only_cookie_attribute = local.owner_template_http_only_cookie_attribute
  oauth_configuration = {
    enabled = true
    dynamic_client_registration = {
      enabled                = true
      allowed_uris           = ["https://chatgpt.com/connector/oauth/*"]
      allow_any_on_localhost = true
      allow_any_on_loopback  = true
    }
    grant = {
      access_token_lifetime = "15m"
      session_duration      = "336h"
    }
  }

  policies = [
    {
      name       = "Allow owner"
      decision   = "allow"
      precedence = 1
      include = [
        {
          email = {
            email = one(local.owner_email_candidates)
          }
        }
      ]
    }
  ]
}

resource "cloudflare_zero_trust_access_service_token" "gateway_windows_runtime" {
  account_id = var.account_id
  name       = "Ordivon Gateway Windows Runtime"
  duration   = "8760h"
  enabled    = true
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "production" {
  account_id = var.account_id
  tunnel_id  = local.production_tunnel_id

  config = {
    ingress = concat(
      local.unmanaged_ingress,
      [
        for key, handoff in local.handoffs : {
          hostname = handoff.hostname
          service  = handoff.service
        }
      ],
      [
        {
          hostname = local.gateway.hostname
          service  = local.gateway.service
        }
      ],
      local.catch_all_ingress,
    )
  }

  depends_on = [
    cloudflare_zero_trust_access_application.handoff,
    cloudflare_zero_trust_access_application.gateway_mcp,
  ]

  lifecycle {
    prevent_destroy = true
  }
}

import {
  to = cloudflare_zero_trust_tunnel_cloudflared_config.production
  id = "${var.account_id}/${local.production_tunnel_id}"
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "native" {
  account_id = var.account_id
  tunnel_id  = local.native_tunnel_id

  config = {
    ingress = concat(
      local.native_unmanaged_ingress,
      [
        {
          hostname = local.gateway.hostname
          service  = "http://127.0.0.1:19000"
        }
      ],
      local.native_catch_all_ingress,
    )
  }

  depends_on = [cloudflare_zero_trust_access_application.gateway_mcp]

  lifecycle {
    prevent_destroy = true
  }
}

import {
  to = cloudflare_zero_trust_tunnel_cloudflared_config.native
  id = "${var.account_id}/${local.native_tunnel_id}"
}

resource "cloudflare_dns_record" "handoff" {
  for_each = local.handoffs

  zone_id = local.production_zone_id
  name    = each.value.hostname
  content = "${local.production_tunnel_id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true

  depends_on = [
    cloudflare_zero_trust_tunnel_cloudflared_config.production,
    cloudflare_zero_trust_tunnel_cloudflared_config.native,
  ]
}

resource "cloudflare_dns_record" "gateway_mcp" {
  zone_id = local.production_zone_id
  name    = local.gateway.hostname
  content = "${local.native_tunnel_id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true

  # The native route must exist before the stable hostname can move to the Windows carrier.
  depends_on = [
    cloudflare_zero_trust_tunnel_cloudflared_config.production,
    cloudflare_zero_trust_tunnel_cloudflared_config.native,
  ]
}
