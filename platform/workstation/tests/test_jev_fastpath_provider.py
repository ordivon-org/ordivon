import hashlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "452c1ad2dd628008f1d5608f28158d76e49e6cc0"


def test_provider_is_exact_commit_and_frozen_upstream_environment():
    text = (ROOT / "ansible/jev-fastpath-provider.yml").read_text()
    assert f"jev_commit: {COMMIT}" in text
    assert "uv\n          - sync" in text
    assert "--frozen" in text
    assert "--no-dev" in text
    assert "m.version('jev-ultrafast') == '0.1.0'" in text
    assert "m.version('browser-harness') == '0.1.13'" in text
    assert "TYPESAFE_API_KEY" not in text
    assert "TEXT_MODEL_API_KEY" not in text


def test_equipment_catalog_binds_exact_realized_entrypoints_when_present():
    catalog = tomllib.loads((ROOT / "workstation/software.toml").read_text())
    rows = catalog["managed_equipment"]
    expected = {
        "jev-ultrafast-0-1-0": "462e36c08c2c79bb4fed27ff3440413fd495352fd1c908570491cf53fbe2947f",
        "browser-harness-0-1-13": "cfe1a11d89aff30a6098276f7b1b34bab6bff94b801606e62da9362de92dc7e5",
    }
    for key, digest in expected.items():
        row = rows[key]
        assert row["execution_target"] == "local_linux"
        assert COMMIT in row["executable"]
        path = Path(row["executable"])
        if path.is_file():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest == row["sha256"]
