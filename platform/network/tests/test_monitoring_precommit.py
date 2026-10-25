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



def test_checked_in_monitoring_probes_have_bound_modules_and_targets():
    owner = _load()
    assert owner.verify_probe_consumer_edges(ROOT / "config") >= 1


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unknown-module", "unknown/ambiguous module"),
        ("missing-module", "unknown/ambiguous module"),
        ("missing-target", "target not forwarded"),
        ("dynamic-module", "dynamically overridden module"),
        ("missing-exporter", "exporter endpoint not bound"),
        ("duplicate-job", "duplicate Prometheus job name"),
    ],
)
def test_cross_config_monitoring_consumer_counterexamples_fail_closed(
    tmp_path, mutation, message,
):
    """Separate upstream config checks cannot establish this cross-file consumer edge."""
    import json
    import subprocess

    owner = _load()
    source = tmp_path / "config"
    source.joinpath("blackbox").mkdir(parents=True)
    source.joinpath("prometheus").mkdir(parents=True)
    source.joinpath("blackbox/blackbox.yml").write_text(
        "modules:\n  http_test:\n    prober: http\n    timeout: 5s\n"
    )
    job = {
        "job_name": "consumer-probe",
        "metrics_path": "/probe",
        "params": {"module": ["http_test"]},
        "static_configs": [{"targets": ["https://example.com/"]}],
        "relabel_configs": [
            {"source_labels": ["__address__"], "target_label": "__param_target"},
            {"target_label": "__address__", "replacement": "127.0.0.1:29115"},
        ],
    }
    if mutation == "unknown-module":
        job["params"]["module"] = ["foreign_module"]
    elif mutation == "missing-module":
        job["params"] = {}
    elif mutation == "missing-target":
        job["relabel_configs"].pop(0)
    elif mutation == "dynamic-module":
        job["relabel_configs"].append(
            {"target_label": "__param_module", "replacement": "foreign_module"}
        )
    elif mutation == "missing-exporter":
        job["relabel_configs"].pop(1)
    jobs = [job]
    if mutation == "duplicate-job":
        jobs.append(dict(job))
    source.joinpath("prometheus/prometheus.yml").write_text(
        json.dumps({"scrape_configs": jobs})
    )
    if mutation in {"unknown-module", "missing-target"}:
        # Independent Prometheus/Blackbox CLI syntax gates do not see the peer config.
        prom = subprocess.run(
            ["promtool", "check", "config", str(source / "prometheus/prometheus.yml")],
            capture_output=True, text=True, check=False,
        )
        assert prom.returncode == 0, prom.stderr
    with pytest.raises(ValueError, match=message):
        owner.verify_probe_consumer_edges(source)


def test_core_validation_invokes_cross_config_consumer_gate():
    taskfile = (ROOT / "Taskfile.yml").read_text()
    native = taskfile.split("  core:validate:", 1)[1].split("  provider:surfshark:validate:", 1)[0]
    assert "monitoring-sourcecut-preflight.py --source config --check-edges" in native
