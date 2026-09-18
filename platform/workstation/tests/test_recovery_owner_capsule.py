from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("owner_capsule_recovery", ROOT / "recovery" / "owner_capsule_recovery.py")
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_finance_is_declarative_owner_capsule() -> None:
    cfg = M.load_owner("finance")
    assert cfg["owner"] == "finance"
    assert cfg["exporter"].endswith("/finance-recovery-capsule")
    assert cfg["tag"] == "finance-owner-recovery"
    assert cfg["retain_snapshots"] == 14


def test_existing_repository_unlocks_stale_locks_before_config_probe(tmp_path: Path) -> None:
    repository = tmp_path / "semantic"
    repository.mkdir()
    (repository / "config").write_bytes(b"restic-config")
    password = tmp_path / "password"
    password.write_text("secret\n")
    cfg = {
        "repository": str(repository),
        "password_file": str(password),
    }
    calls: list[list[str]] = []

    def fake_checked(args, *, env=None, timeout=60):
        calls.append(list(args))
        return subprocess.CompletedProcess(args, 0, "", "")

    with mock.patch.object(M, "checked", side_effect=fake_checked):
        M.require_transport(cfg)

    restic_calls = [call for call in calls if call and call[0] == M.RESTIC]
    assert restic_calls[0] == M.restic_command("unlock")
    assert restic_calls[1] == M.restic_command("cat", "config")
    assert "--remove-all" not in restic_calls[0]


def test_backup_snapshot_id_requires_one_summary() -> None:
    text = '\n'.join([
        json.dumps({"message_type": "status", "percent_done": 0.5}),
        json.dumps({"message_type": "summary", "snapshot_id": "abc123"}),
    ])
    assert M.snapshot_id_from_backup_json(text) == "abc123"
    for bad in ("", json.dumps({"message_type": "status"})):
        try:
            M.snapshot_id_from_backup_json(bad)
        except RuntimeError:
            pass
        else:
            raise AssertionError("missing restic summary was accepted")


def test_daily_backup_does_not_run_retention_or_check() -> None:
    cfg = M.load_owner("finance")
    calls: list[list[str]] = []
    capsule_tree = {"treeSha256": "tree", "files": 1, "bytes": 1, "entries": []}
    def fake_checked(args, *, env=None, timeout=60):
        calls.append(list(args))
        if "--export" in args:
            out = Path(args[-1]); out.mkdir(parents=True); (out / "x").write_bytes(b"x")
            return subprocess.CompletedProcess(args, 0, "exported\n", "")
        if "backup" in args:
            return subprocess.CompletedProcess(args, 0, json.dumps({"message_type":"summary","snapshot_id":"snap-1"})+"\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")
    with mock.patch.object(M, "require_transport"), \
         mock.patch.object(M, "resolved_exporter", return_value=Path("/bin/true")), \
         mock.patch.object(M, "capsule_tree", return_value=capsule_tree), \
         mock.patch.object(M, "checked", side_effect=fake_checked), \
         mock.patch.object(M, "verify_restored_snapshot", return_value={"snapshotId":"snap-1"}), \
         mock.patch.object(M, "write_receipt"):
        result = M.backup_locked(cfg)
    flat = [item for call in calls for item in call]
    assert result["snapshotId"] == "snap-1"
    assert "forget" not in flat
    assert "prune" not in flat
    assert "check" not in flat
    assert result["maintenanceDeferred"] is True


def test_retention_is_separate_provider_native_prune() -> None:
    cfg = M.load_owner("finance")
    calls = []
    def fake_checked(args, *, env=None, timeout=60):
        calls.append((list(args), timeout))
        return subprocess.CompletedProcess(args, 0, "", "")
    with mock.patch.object(M, "require_transport"), mock.patch.object(M, "checked", side_effect=fake_checked):
        result = M.retention(cfg)
    command = calls[-1][0]
    assert "forget" in command and "--prune" in command
    assert "--keep-last" in command and "14" in command
    assert result["status"] == "pass"


def test_monthly_check_is_separate() -> None:
    cfg = M.load_owner("finance")
    with mock.patch.object(M, "require_transport"), mock.patch.object(
        M, "checked", return_value=subprocess.CompletedProcess([], 0, "check ok\n", "")
    ) as checked:
        result = M.repository_check(cfg)
    assert "check" in checked.call_args.args[0]
    assert result["status"] == "pass"

def test_finance_legacy_v0_snapshot_remains_restorable() -> None:
    cfg = M.load_owner("finance")
    legacy_tree = {"treeSha256": "legacy-tree", "files": 1, "bytes": 6, "entries": []}
    transport = {
        "schemaVersion": 0,
        "kind": "ordivon.workstation.finance-recovery-transport.v0",
        "owner": "finance",
        "capsule": {"treeSha256": "legacy-tree", "files": 1, "bytes": 6},
    }

    def fake_checked(args, *, env=None, timeout=60):
        if "restore" in args:
            target = Path(args[args.index("--target") + 1])
            root = target / "legacy" / "finance-recovery-custody"
            (root / "capsule").mkdir(parents=True)
            (root / "capsule" / "x").write_bytes(b"legacy")
            (root / "transport.json").write_text(json.dumps(transport) + "\n")
            return subprocess.CompletedProcess(args, 0, "", "")
        if "--verify" in args:
            return subprocess.CompletedProcess(args, 0, "verified\n", "")
        raise AssertionError(args)

    metadata = {"paths": ["/legacy/finance-recovery-custody"]}
    with mock.patch.object(M, "snapshot_metadata", return_value=metadata), \
         mock.patch.object(M, "staging_parent", return_value=Path("/tmp")), \
         mock.patch.object(M, "capsule_tree", return_value=legacy_tree), \
         mock.patch.object(M, "checked", side_effect=fake_checked):
        result = M.verify_restored_snapshot(cfg, "legacy", exporter=Path("/bin/true"))
    assert result["ownerVerifySucceeded"] is True
    assert result["transportKind"] == "ordivon.workstation.finance-recovery-transport.v0"
