"""Consumer contract: prevent an old repo Network source from erasing live monitors."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/monitoring-sourcecut-preflight.py"
CONFIGS = ("blackbox/blackbox.yml", "prometheus/prometheus.yml")


def _load():
    spec = importlib.util.spec_from_file_location("network_monitor_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _files(root: Path, *, blackbox: bytes = b"modules: {}\\n", prometheus: bytes = b"scrape_configs: []\\n"):
    for name, data in zip(CONFIGS, (blackbox, prometheus), strict=True):
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)


@pytest.mark.parametrize("root_link", ["source", "live", "dangling-live"])
def test_monitoring_preflight_rejects_root_symlink_before_install(tmp_path, root_link):
    """A symlink at the root escapes the two declared monitoring Owner trees."""
    owner = _load()
    source, live = tmp_path / "source", tmp_path / "live"
    if root_link == "source":
        outside = tmp_path / "outside-source"
        _files(outside)
        source.symlink_to(outside, target_is_directory=True)
    else:
        _files(source)
        outside = tmp_path / "outside-live"
        if root_link == "live":
            outside.mkdir()
        live.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="monitoring root"):
        owner.verify(source, live)


def test_first_install_and_idempotent_sourcecut(tmp_path):
    owner = _load()
    source, live = tmp_path / "source", tmp_path / "live"
    _files(source)
    assert owner.verify(source, live) == "FIRST_INSTALL"
    _files(live)
    assert owner.verify(source, live) == "IDENTICAL_SOURCECUT"


@pytest.mark.parametrize("which", ["blackbox", "prometheus"])
def test_missing_or_partial_live_sourcecut_fails_closed(tmp_path, which):
    owner = _load()
    source, live = tmp_path / "source", tmp_path / "live"
    _files(source)
    path = live / CONFIGS[0 if which == "blackbox" else 1]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((source / CONFIGS[0 if which == "blackbox" else 1]).read_bytes())
    with pytest.raises(ValueError, match="incomplete"):
        owner.verify(source, live)


@pytest.mark.parametrize("which", ["blackbox", "prometheus"])
def test_live_consumer_drift_refuses_overwrite(tmp_path, which):
    owner = _load()
    source, live = tmp_path / "source", tmp_path / "live"
    _files(source)
    _files(live)
    drifted = live / CONFIGS[0 if which == "blackbox" else 1]
    drifted.write_bytes(drifted.read_bytes() + b"# live extra consumer\\n")
    before = drifted.read_bytes()
    with pytest.raises(ValueError, match="differs"):
        owner.verify(source, live)
    assert drifted.read_bytes() == before



@pytest.mark.parametrize("area", ["source", "live"])
@pytest.mark.parametrize("name", [
    "prometheus/consumer.rules.yml",
    "blackbox/scoped-consumer.yaml",
])
def test_unlisted_monitoring_configs_are_not_accepted(tmp_path, area, name):
    owner = _load()
    source, live = tmp_path / "source", tmp_path / "live"
    _files(source)
    _files(live)
    extra = (source if area == "source" else live) / name
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("groups: []\n")
    with pytest.raises(ValueError, match="unmanaged monitoring"):
        owner.verify(source, live)
    assert extra.read_text() == "groups: []\n"


def test_first_install_does_not_ignore_preexisting_monitoring_rules(tmp_path):
    owner = _load()
    source, live = tmp_path / "source", tmp_path / "live"
    _files(source)
    extra = live / "prometheus/consumer.rules.yml"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("groups: []\n")
    with pytest.raises(ValueError, match="unmanaged monitoring"):
        owner.verify(source, live)


def test_core_install_checks_drift_before_any_live_writes():
    taskfile = (ROOT / "Taskfile.yml").read_text()
    core = taskfile.split("  core:install:", 1)[1].split("  core:verify:", 1)[0]
    guard = "scripts/monitoring-sourcecut-preflight.py"
    assert guard in core
    assert core.index(guard) < core.index("install -d")
    assert core.index(guard) < core.index("install -m")
