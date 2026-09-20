import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R = load_module(
    "runtime_control_provider",
    "workstation/providers/runtime_control_provider.py",
)
S = load_module(
    "linux_service_observer",
    "workstation/providers/linux_service_observer.py",
)


def test_runtime_control_provider_uses_exact_read_only_commands(monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        if argv[0] == R.RUNTIME_STATUS:
            return SimpleNamespace(stdout=json.dumps({"status": "healthy"}), stderr="", returncode=0)
        return SimpleNamespace(
            stdout=json.dumps({"integrityCheck": "ok", "violationCount": 0}),
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(R.subprocess, "run", fake_run)
    status = R.status()
    assert status["healthy"] is True
    assert status["mutationAttempted"] is False
    assert calls == [
        [R.RUNTIME_STATUS, "--health", "--json"],
        [
            R.RUNTIME_DOCTOR,
            "inspect",
            "--database",
            R.REGISTRY_DB,
            "--store-root",
            R.STORE_ROOT,
            "--pretty",
        ],
    ]


def test_service_observer_has_fixed_allowlist_and_no_mutation(monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(stdout="active\n", stderr="", returncode=0)

    monkeypatch.setattr(S.subprocess, "run", fake_run)
    result = S.probe_control_plane()
    assert result["healthy"] is True
    assert result["mutationAttempted"] is False
    assert set(result["units"]) == set(S.CONTROL_PLANE_UNITS)
    assert all(call[:2] == ["/usr/bin/systemctl", "is-active"] for call in calls)
