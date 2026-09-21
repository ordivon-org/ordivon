from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "recovery_generation_v2", ROOT / "recovery" / "workstation_recovery_generation.py"
)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture_source(root: Path) -> tuple[Path, Path]:
    repository = root / "ordivon"
    owner = repository / "platform" / "workstation"
    recovery_dir = owner / "recovery"
    recovery_dir.mkdir(parents=True)
    for name in [
        "backup_authority_material.py",
        "backup_semantic_state.py",
        "owner_capsule_recovery.py",
        "restic_mirror_verify.py",
    ]:
        (recovery_dir / name).write_text(f'print("{name}")\n')
    (recovery_dir / "workstation_recovery_generation.py").write_text(
        (ROOT / "recovery" / "workstation_recovery_generation.py").read_text()
    )
    contract = "\n".join(
        [
            'role = "ordivon-monorepo-workstation-recovery"',
            "",
            "[recovery]",
            f'control_repository = "{repository}"',
            'control_snapshot_tag = "ordivon-monorepo-control"',
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
        ]
    )
    (recovery_dir / "recovery.toml").write_text(contract)
    subprocess.run(["/usr/bin/git", "init", str(repository)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "config", "user.name", "Fixture"], check=True
    )
    subprocess.run(["/usr/bin/git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "commit", "-m", "fixture"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return repository, owner


def test_generation_binds_monorepo_source_and_workstation_owner() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        repository, owner = fixture_source(base)
        result = M.provision_generation(owner)
        installed = Path(result["path"])
        launcher = (installed / "bin/workstation-backup").read_text()
        assert result["status"] == "pass" and result["current"]
        assert result["sourceRepository"] == str(repository.resolve())
        assert result["ownerRelativePath"] == "platform/workstation"
        assert "OWNER_RELATIVE=platform/workstation" in launcher
        assert 'CONTROL_REPOSITORY=' + str(repository) in launcher
        assert "CONTROL_SNAPSHOT_TAG=ordivon-monorepo-control" in launcher
        assert '"$OWNER_ROOT/recovery/backup_authority_material.py"' in launcher
        assert '"$OWNER_ROOT/recovery/backup_semantic_state.py"' in launcher
        assert '"$OWNER_ROOT/recovery/restic_mirror_verify.py"' in launcher
        assert "--tag workstation-v2-control" not in launcher
        owner_launcher = (installed / "bin/owner-capsule-recovery").read_text()
        assert '"$OWNER_ROOT/recovery/owner_capsule_recovery.py"' in owner_launcher
        assert result["ownerCapsuleLauncherSha256"].startswith("sha256:")
        manifest = json.loads((installed / "generation.json").read_text())
        assert manifest["schemaVersion"] == 1
        assert manifest["kind"] == "ordivon.workstation.recovery-generation.v1"
        assert manifest["ownerRelativePath"] == "platform/workstation"
        assert manifest["controlRepository"] == str(repository)
        assert manifest["createdFrom"]["sourceRepositoryPath"] == str(repository.resolve())
        assert manifest["createdFrom"]["ownerSourcePath"] == str(owner.resolve())


def test_generation_rejects_dirty_monorepo_even_when_owner_is_clean() -> None:
    with tempfile.TemporaryDirectory() as raw:
        repository, owner = fixture_source(Path(raw))
        (repository / "outside-owner-dirty").write_text("x")
        try:
            M.provision_generation(owner)
        except M.RecoveryGenerationError as error:
            assert "clean source" in str(error)
        else:
            raise AssertionError("dirty monorepo source was accepted")


def test_contract_digest_changes_with_recovery_implementation() -> None:
    with tempfile.TemporaryDirectory() as raw:
        _, owner = fixture_source(Path(raw))
        before = M.recovery_contract_digest(owner)
        p = owner / "recovery/backup_semantic_state.py"
        p.write_text(p.read_text() + "# change\n")
        assert M.recovery_contract_digest(owner) != before


def test_contract_digest_changes_with_minimal_contract() -> None:
    with tempfile.TemporaryDirectory() as raw:
        _, owner = fixture_source(Path(raw))
        before = M.recovery_contract_digest(owner)
        p = owner / "recovery/recovery.toml"
        p.write_text(p.read_text().replace("retain_control_snapshots = 14", "retain_control_snapshots = 13"))
        assert M.recovery_contract_digest(owner) != before


def test_repository_root_is_derived_from_owner_path() -> None:
    with tempfile.TemporaryDirectory() as raw:
        repository, owner = fixture_source(Path(raw))
        assert M._repository_root(owner) == repository.resolve()
