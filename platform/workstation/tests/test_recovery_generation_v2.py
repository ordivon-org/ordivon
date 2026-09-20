from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("recovery_generation_v2", ROOT / "recovery" / "workstation_recovery_generation.py")
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture_source(root: Path) -> Path:
    source = root / "source"
    recovery_dir = source / "recovery"
    recovery_dir.mkdir(parents=True)
    for name in ["backup_authority_material.py", "backup_semantic_state.py", "owner_capsule_recovery.py", "restic_mirror_verify.py"]:
        (recovery_dir / name).write_text(f'print("{name}")\n')
    (recovery_dir / "workstation_recovery_generation.py").write_text(
        (ROOT / "recovery" / "workstation_recovery_generation.py").read_text()
    )
    control = root / "live-control"
    (control / ".git").mkdir(parents=True)
    contract = "\n".join([
        "[recovery]",
        f'control_repository = "{control}"',
        'control_snapshot_tag = "workstation-v2-control"',
        f'primary_repository = "{root / "primary"}"',
        'retain_control_snapshots = 14',
        f'restic_mirror = "{root / "mirror"}"',
        f'restic_password_file = "{root / "password"}"',
        f'semantic_repository = "{root / "semantic"}"',
        f'backup_generation_root = "{root / "install"}"',
        "",
        "[owner_capsules.finance]",
        'exporter = "/bin/true"',
        f'repository = "{root / "semantic"}"',
        f'password_file = "{root / "password"}"',
        'tag = "finance-owner-recovery"',
        f'receipt = "{root / "receipt.json"}"',
        f'attempt = "{root / "attempt.json"}"',
        f'staging_parent = "{root / "stage"}"',
        'retain_snapshots = 14',
        'backup_timeout_seconds = 600',
        'restore_timeout_seconds = 300',
        'maintenance_timeout_seconds = 1800',
        'check_timeout_seconds = 1800',
        "",
    ])
    (recovery_dir / "recovery.toml").write_text(contract)
    subprocess.run(["/usr/bin/git", "init", str(source)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["/usr/bin/git", "-C", str(source), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["/usr/bin/git", "-C", str(source), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["/usr/bin/git", "-C", str(source), "add", "."], check=True)
    subprocess.run(["/usr/bin/git", "-C", str(source), "commit", "-m", "fixture"], check=True, stdout=subprocess.DEVNULL)
    return source


def test_generation_uses_v2_recovery_kernel_and_tag() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        source = fixture_source(base)
        result = M.provision_generation(source)
        installed = Path(result["path"])
        launcher = (installed / "bin/workstation-backup").read_text()
        assert result["status"] == "pass" and result["current"]
        assert "recovery/backup_authority_material.py" in launcher
        assert "recovery/backup_semantic_state.py" in launcher
        assert "recovery/restic_mirror_verify.py" in launcher
        assert "CONTROL_SNAPSHOT_TAG=workstation-v2-control" in launcher
        assert '--tag "$CONTROL_SNAPSHOT_TAG"' in launcher
        assert "--tag workstation-lab" not in launcher
        owner_launcher = (installed / "bin/owner-capsule-recovery").read_text()
        assert "recovery/owner_capsule_recovery.py" in owner_launcher
        assert result["ownerCapsuleLauncherSha256"].startswith("sha256:")
        manifest = json.loads((installed / "generation.json").read_text())
        assert manifest["controlRepository"] == str(base / "live-control")
        assert manifest["ownerCapsuleLauncher"]["relativePath"] == "bin/owner-capsule-recovery"


def test_generation_rejects_dirty_source() -> None:
    with tempfile.TemporaryDirectory() as raw:
        source = fixture_source(Path(raw))
        (source / "dirty").write_text("x")
        try:
            M.provision_generation(source)
        except M.RecoveryGenerationError as error:
            assert "clean source" in str(error)
        else:
            raise AssertionError("dirty source was accepted")


def test_contract_digest_changes_with_recovery_implementation() -> None:
    with tempfile.TemporaryDirectory() as raw:
        source = fixture_source(Path(raw))
        before = M.recovery_contract_digest(source)
        p = source / "recovery/backup_semantic_state.py"
        p.write_text(p.read_text() + "# change\n")
        assert M.recovery_contract_digest(source) != before


def test_contract_digest_changes_with_minimal_contract() -> None:
    with tempfile.TemporaryDirectory() as raw:
        source = fixture_source(Path(raw))
        before = M.recovery_contract_digest(source)
        p = source / "recovery/recovery.toml"
        p.write_text(p.read_text().replace("retain_control_snapshots = 14", "retain_control_snapshots = 13"))
        assert M.recovery_contract_digest(source) != before
