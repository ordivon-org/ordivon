from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import artifact_python_environment as m


def desired():
    lock = m.load_lock()
    project = {
        "project": "/fixture",
        "pyprojectSha256": lock["uvProject"]["pyprojectSha256"],
        "uvLockSha256": lock["uvProject"]["uvLockSha256"],
    }
    python = {"resolvedPath": "/fixture/python", "sha256": "sha256:" + "1" * 64}
    spec = m.generation_spec(lock, project, python)
    gid = hashlib.sha256(m.canonical(spec)).hexdigest()
    return lock, project, python, spec, gid


def test_existing_generation_cannot_relabel_binding(tmp_path):
    lock, project, python, spec, gid = desired()
    final = tmp_path / "generations" / gid
    final.mkdir(parents=True)
    (final / "binding.json").write_text(
        json.dumps({**spec, "generationId": gid, "pythonRuntime": "3.14.0"})
    )
    with pytest.raises(RuntimeError, match="binding"):
        m.build_generation(tmp_path, lock, project, python)


def test_status_rejects_directory_outside_generation_namespace(tmp_path):
    wrong = tmp_path / "other"
    wrong.mkdir()
    (wrong / "binding.json").write_text("{}")
    (tmp_path / "current").symlink_to(wrong)
    with patch.object(m, "probe_wrapper", return_value={"status": "PASS"}):
        status = m.status(tmp_path)
    assert not status["ready"]


def test_rejected_candidate_preserves_old_current(tmp_path):
    lock, project, python, spec, gid = desired()
    lock["stableRoot"] = str(tmp_path)
    old = tmp_path / "generations" / "old"
    old.mkdir(parents=True)
    final = old.parent / gid
    final.mkdir()
    (tmp_path / "current").symlink_to(old)
    with (
        patch.object(m, "MAIN", m.ROOT),
        patch.object(m, "load_lock", return_value=lock),
        patch.object(m, "project_status", return_value=project),
        patch.object(m, "python_status", return_value=python),
        patch.object(m, "build_generation", return_value=(gid, final, spec)),
        patch.object(m, "qualify_generation", side_effect=RuntimeError("candidate rejected")),
        patch.object(m, "status", return_value={"ready": False}),
    ):
        with pytest.raises(RuntimeError):
            m.apply()
    assert (tmp_path / "current").resolve() == old


def test_post_publish_failure_restores_exact_previous_link(tmp_path):
    lock, project, python, spec, gid = desired()
    lock["stableRoot"] = str(tmp_path)
    old = tmp_path / "generations" / "old"
    old.mkdir(parents=True)
    final = old.parent / gid
    final.mkdir()
    current = tmp_path / "current"
    current.symlink_to(Path("generations/old"))
    with (
        patch.object(m, "MAIN", m.ROOT),
        patch.object(m, "load_lock", return_value=lock),
        patch.object(m, "project_status", return_value=project),
        patch.object(m, "python_status", return_value=python),
        patch.object(m, "build_generation", return_value=(gid, final, spec)),
        patch.object(m, "qualify_generation", return_value=(spec, {"status": "PASS"})),
        patch.object(m, "status", return_value={"ready": False}),
    ):
        with pytest.raises(RuntimeError, match="publication did not verify"):
            m.apply()
    assert current.readlink() == Path("generations/old")
