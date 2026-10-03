from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "ansible/runtime-lifecycle-service.yml"


def test_runtime_lifecycle_realization_uses_mature_ansible_systemd_primitives() -> None:
    text = PLAYBOOK.read_text(encoding="utf-8")

    assert "ansible.builtin.stat:" in text
    assert "checksum_algorithm: sha256" in text
    assert "ansible.builtin.copy:" in text
    assert "backup: true" in text
    assert "ansible.builtin.systemd_service:" in text
    assert "daemon_reload: true" in text
    assert "FragmentPath" in text
    assert "LoadState" in text


def test_runtime_lifecycle_realization_preserves_owner_boundaries() -> None:
    text = PLAYBOOK.read_text(encoding="utf-8")

    assert "services/runtime/packaging/systemd/ordivon-runtime-lifecycle.service" in text
    assert "/etc/systemd/system/ordivon-runtime-lifecycle.service" in text
    assert "runtime_lifecycle_expected_sha256" in text
    assert "policy_file_mutated: false" in text

    assert "workspace-retention.json" not in text
    assert "/var/lib/ordivon/workstation/providers/receipts" not in text
    assert "workflow" not in text.lower()
    assert "scheduler" not in text.lower()


def test_runtime_lifecycle_realization_has_explicit_failed_postcondition_rollback() -> None:
    text = PLAYBOOK.read_text(encoding="utf-8")

    assert "rescue:" in text
    assert "runtime_lifecycle_install.backup_file" in text
    assert "remote_src: true" in text
    assert "state: absent" in text
    assert "rollback was attempted" in text
