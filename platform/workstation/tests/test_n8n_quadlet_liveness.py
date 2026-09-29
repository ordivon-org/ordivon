from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POD = ROOT / "n8n" / "ordivon-n8n.pod"
PLAYBOOK = ROOT / "ansible" / "n8n.yml"


def test_n8n_quadlet_attaches_to_user_default_target() -> None:
    text = POD.read_text(encoding="utf-8")
    assert "[Install]" in text
    assert "WantedBy=default.target" in text


def test_n8n_playbook_uses_quadlet_generator_not_systemctl_enable() -> None:
    text = PLAYBOOK.read_text(encoding="utf-8")
    assert "systemctl --user enable ordivon-n8n-pod.service" not in text
    assert "systemctl --user is-enabled ordivon-n8n-pod.service" not in text
    assert "systemctl --user daemon-reload" in text
    assert "systemctl --user show ordivon-n8n-pod.service -p WantedBy --value" in text
    assert "grep -Fx default.target" in text


def test_n8n_playbook_preserves_runtime_start_and_restart_convergence() -> None:
    text = PLAYBOOK.read_text(encoding="utf-8")
    assert "systemctl --user start ordivon-n8n-pod.service" in text
    assert "systemctl --user restart ordivon-n8n-pod.service" in text
    assert "url: http://127.0.0.1:5678/healthz/readiness" in text


def test_live_acceptance_checks_default_target_attachment() -> None:
    script = (ROOT / "scripts" / "verify-n8n-rootless.sh").read_text(encoding="utf-8")
    assert "systemctl --user show ordivon-n8n-pod.service -p WantedBy --value" in script
    assert "grep -Fx default.target" in script
