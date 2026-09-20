from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "ansible/retire-wsl-cloudflare-canary.yml"

def test_retirement_uses_systemd_and_removes_only_canary_unit():
    text = PLAYBOOK.read_text()
    assert "ansible.builtin.systemd_service" in text
    assert "ordivon-cloudflare-canary.service" in text
    assert "state: stopped" in text
    assert "enabled: false" in text
    assert "/etc/systemd/system/ordivon-cloudflare-canary.service" in text
    assert "state: absent" in text
    assert "daemon_reload: true" in text
    assert "ordivon-cloudflare-production-a.service" not in text
    assert "ordivon-cloudflare-production-b.service" not in text

def test_retirement_does_not_delete_canary_credential_material():
    text = PLAYBOOK.read_text()
    assert "/etc/cloudflared/canary.env" not in text
    assert "windows-runtime-canary.token" not in text
