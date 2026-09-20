from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOFU = ROOT / "tofu" / "agent-birth-handoff"


def test_agent_birth_handoff_pins_current_stable_toolchain():
    versions = (TOFU / "versions.tf").read_text(encoding="utf-8")
    assert 'required_version = "= 1.12.6"' in versions
    assert 'version = "= 5.25.0"' in versions


def test_handoff_surface_is_exact_and_loopback_origin_only():
    source = (TOFU / "main.tf").read_text(encoding="utf-8")
    for instance in (11, 12, 13):
        assert f'hostname    = "handoff-{instance}.ordivon.com"' in source
        assert f'service     = "http://127.0.0.1:160{instance}"' in source
    assert 'name       = "ordivon-wsl"' in source
    assert 'domain     = "skills-mcp.ordivon.com"' in source
    assert 'session_duration           = "15m"' in source
    assert "enable_binding_cookie      = true" in source
    assert "http_only_cookie_attribute = true" in source


def test_access_precedes_tunnel_and_dns_publication():
    source = (TOFU / "main.tf").read_text(encoding="utf-8")
    assert "depends_on = [cloudflare_zero_trust_access_application.handoff]" in source
    assert "depends_on = [cloudflare_zero_trust_tunnel_cloudflared_config.production]" in source


def test_existing_tunnel_is_imported_and_never_destroyed():
    source = (TOFU / "main.tf").read_text(encoding="utf-8")
    assert 'to = cloudflare_zero_trust_tunnel_cloudflared_config.production' in source
    assert 'id = "${var.account_id}/${local.production_tunnel_id}"' in source
    assert "prevent_destroy = true" in source
    assert "unmanaged_ingress" in source
    assert "catch_all_ingress" in source


def test_git_source_contains_no_cloudflare_secret_or_owner_identity():
    source_files = [
        *TOFU.glob("*.tf"),
        TOFU / "README.md",
        TOFU / "tofurc",
        TOFU / ".gitignore",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    lowered = text.lower()
    assert "api_token" not in lowered
    assert "cloudflare-account-api-token" not in lowered
    assert "@gmail." not in lowered
    assert "@outlook." not in lowered


def test_ephemeral_and_private_state_are_not_git_inputs():
    ignore = (TOFU / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".terraform/" in ignore
    assert "*.tfplan" in ignore
    assert "*.tfstate" in ignore
    versions = (TOFU / "versions.tf").read_text(encoding="utf-8")
    assert "/var/lib/ordivon/operations-v2/tofu/agent-birth-handoff/terraform.tfstate" in versions
