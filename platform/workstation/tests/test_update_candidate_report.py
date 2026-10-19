from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/update_candidate_report.py"
spec = importlib.util.spec_from_file_location("update_candidate_report", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_native_read_only_command_set_and_explicit_unknowns():
    calls = []

    def probe(command, *, cwd, timeout):
        calls.append(command)
        if command[0] == "checkupdates":
            return {"returncode": 0, "stdout": "curl 8.1 -> 8.2\n"}
        if command[0] == "mise":
            return {
                "returncode": 0,
                "stdout": '{"node": {"requested":"26", "current":"26.1", "latest":"26.2"}}',
            }
        return {"returncode": 0, "stdout": ""}

    result = module.collect("/tmp", probe=probe, mise_scopes=["."])
    assert calls == [
        ["checkupdates", "--nocolor"],
        ["mise", "outdated", "--bump", "--json", "--local"],
        ["podman", "auto-update", "--dry-run", "--format", "json"],
    ]
    assert result["checks"]["arch"]["items"][0]["package"] == "curl"
    assert result["checks"]["mise"]["items"][0]["latest"] == "26.2"
    assert result["checks"]["podman"]["state"] == "no_eligible_containers"
    assert result["effects"]["containersRestarted"] == 0


def test_checkupdates_empty_and_failure_have_different_meanings():
    assert module.normalize_arch({"returncode": 2, "stdout": ""})["state"] == "current"
    assert module.normalize_arch({"returncode": 1, "stdout": ""})["state"] == "unknown"
    assert module.normalize_mise({"returncode": 1, "stdout": ""})["state"] == "unknown"
    assert module.normalize_podman({"returncode": 1, "stdout": ""})["state"] == "unknown"
    assert module.normalize_mise({"returncode": 0, "stdout": "INVALID"})["state"] == "unknown"
    assert module.normalize_podman({"returncode": 0, "stdout": "{}"})["state"] == "unknown"


def test_run_probe_does_not_try_to_fix_missing_tools(monkeypatch):
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should never execute")),
    )
    assert module.run_probe(["unknown"], cwd="/tmp", timeout=1)["state"] == "missing"


def test_atomic_output_is_private_and_contains_no_automatic_effects(tmp_path):
    report = {
        "schemaVersion": 1,
        "checks": {"arch": {"state": "current", "items": []}},
        "effects": {"packagesUpgraded": 0, "containersRestarted": 0},
    }
    path = tmp_path / "evidence/current.json"
    module.store(report, path)
    assert json.loads(path.read_text()) == report
    assert path.stat().st_mode & 0o777 == 0o600
    assert not list(path.parent.glob(".update-candidates-*"))


def test_multiple_scopes_never_claim_current_when_one_fails(tmp_path):
    (tmp_path / "game").mkdir()
    (tmp_path / "media").mkdir()

    def probe(command, *, cwd, timeout):
        if cwd.endswith("media"):
            return {"state": "unknown", "items": [], "reason": "probe_timeout"}
        return {
            "returncode": 0,
            "stdout": '{"node": {"requested":"26", "current":"26.1", "latest":"27.0", "bump":"27"}}',
        }

    result = module.check_mise_scopes(
        str(tmp_path),
        ["game", "media"],
        probe=probe,
    )
    assert result["state"] == "partial"
    assert result["scopesChecked"] == result["scopesTotal"] == 2
    assert result["items"][0]["scope"] == "game"
    assert result["items"][0]["bump"] == "27"
    assert result["scopes"][1]["reason"] == "probe_timeout"


def test_untracked_or_invalid_scopes_are_visible_as_unknown(tmp_path):
    result = module.check_mise_scopes(str(tmp_path), ["missing"], probe=lambda **kw: None)
    assert result["state"] == "unknown"
    assert result["scopes"][0]["reason"] == "invalid_scope"


def test_mise_scope_search_only_uses_git_tracked_files(tmp_path):
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "mise.toml").write_text('[tools]\\nnode="26"\\n')
    (tmp_path / "game").mkdir()
    (tmp_path / "game" / "mise.toml").write_text('[tools]\\npython="3.14"\\n')
    (tmp_path / "untracked").mkdir()
    (tmp_path / "untracked" / "mise.toml").write_text('[tools]\\nnode="24"\\n')
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "mise.toml", "game/mise.toml"],
        check=True,
    )
    assert module.tracked_mise_scopes(str(tmp_path)) == [".", "game"]


def test_update_report_binds_exact_source_and_rejects_drift(monkeypatch):
    clean = {"revision": "a" * 40, "dirty": False}
    changed = {"revision": "b" * 40, "dirty": False}
    dirty = {"revision": "a" * 40, "dirty": True}

    def probe(command, *, cwd, timeout):
        return {"state": "missing", "items": [], "reason": "test-only"}

    sequence = iter([clean, clean])
    monkeypatch.setattr(module, "source_snapshot", lambda _: next(sequence), raising=False)
    result = module.collect("/tmp", probe=probe, mise_scopes=[])
    assert result["sourceRevision"] == "a" * 40
    assert result["sourceStanding"] == "stable"

    sequence = iter([clean, changed])
    result = module.collect("/tmp", probe=probe, mise_scopes=[])
    assert result["sourceRevision"] is None
    assert result["sourceStanding"] == "changed_or_dirty"

    sequence = iter([clean, dirty])
    result = module.collect("/tmp", probe=probe, mise_scopes=[])
    assert result["sourceRevision"] is None
    assert result["sourceStanding"] == "changed_or_dirty"


def test_source_snapshot_checks_git_and_worktree_currentness(tmp_path):
    import subprocess

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=12,
        )

    git("init", "-q")
    target = tmp_path / "tracked.txt"
    target.write_text("first\n")
    git("add", "tracked.txt")
    git(
        "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline"
    )
    clean = module.source_snapshot(str(tmp_path))
    assert len(clean["revision"]) == 40
    assert clean["dirty"] is False

    target.write_text("changed\n")
    assert module.source_snapshot(str(tmp_path))["dirty"] is True
    assert module.source_snapshot(str(tmp_path / "missing"))["revision"] is None
