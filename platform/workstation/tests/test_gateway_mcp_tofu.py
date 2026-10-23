from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "tofu" / "agent-birth-handoff" / "main.tf"
OUTPUTS = ROOT / "tofu" / "agent-birth-handoff" / "outputs.tf"


def test_gateway_reuses_the_single_existing_production_tunnel_owner() -> None:
    text = MAIN.read_text(encoding="utf-8")
    assert text.count('resource "cloudflare_zero_trust_tunnel_cloudflared_config" "production"') == 1
    assert 'hostname = "gateway-mcp.ordivon.com"' in text
    assert 'service  = "http://127.0.0.1:8899"' in text
    assert "local.managed_hostnames" in text
    assert "local.catch_all_ingress" in text
    assert "prevent_destroy = true" in text


def test_gateway_access_app_declares_managed_oauth_for_remote_mcp_clients() -> None:
    text = MAIN.read_text(encoding="utf-8")
    assert 'resource "cloudflare_zero_trust_access_application" "gateway_mcp"' in text
    assert 'type                       = "self_hosted"' in text
    assert "oauth_configuration = {" in text
    assert "dynamic_client_registration = {" in text
    assert 'allowed_uris' in text
    assert '"https://chatgpt.com/connector/oauth/*"' in text
    assert "allow_any_on_localhost = true" in text
    assert "allow_any_on_loopback  = true" in text
    assert 'access_token_lifetime = "15m"' in text
    assert 'session_duration      = "336h"' in text
    assert "owner_template_oauth_configuration" not in text
    assert "allowed_idps               = toset(local.owner_template_allowed_idps)" in text
    assert "one(local.owner_email_candidates)" in text
    assert "client_secret" not in text.lower()
    assert "api_token" not in text.lower()


def test_gateway_dns_is_published_only_after_tunnel_configuration() -> None:
    text = MAIN.read_text(encoding="utf-8")
    section = text.split('resource "cloudflare_dns_record" "gateway_mcp"', 1)[1]
    assert "cloudflare_zero_trust_tunnel_cloudflared_config.production" in section
    assert "cloudflare_zero_trust_tunnel_cloudflared_config.native" in section


def test_gateway_outputs_separate_public_metadata_from_sensitive_machine_identity() -> None:
    text = OUTPUTS.read_text(encoding="utf-8")
    assert 'output "gateway_mcp_hostname"' in text
    assert 'output "gateway_mcp_audience"' in text
    assert 'output "gateway_windows_access_service_token_id"' in text
    assert 'output "gateway_windows_access_client_id"' in text
    assert 'output "gateway_windows_access_client_secret"' in text

    secret_section = text.split(
        'output "gateway_windows_access_client_secret"', 1
    )[1]
    assert "client_secret" in secret_section
    assert "sensitive   = true" in secret_section

    public_prefix = text.split('output "gateway_windows_access_service_token_id"', 1)[0]
    assert "client_secret" not in public_prefix.lower()
