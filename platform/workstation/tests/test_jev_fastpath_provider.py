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


def test_external_provider_uv_effects_use_exact_workstation_mise_owner():
    # Local Main c8fea848 documented the real owner requirement; the current
    # Ansible consumers must not regress to an ambient /usr/bin/uv executable.
    for name, count in (("jev-fastpath-provider.yml", 1),
                        ("ppt-master-provider.yml", 2)):
        source = (ROOT / "ansible" / name).read_text()
        assert "- /usr/bin/uv" not in source
        assert source.count("- /usr/bin/mise") == count
        assert source.count('''- "{{ playbook_dir }}/.."''') == count
        assert source.count("- exec") == count
        assert source.count("\n          - --\n") == count
        assert source.count("MISE_AUTO_INSTALL: 'false'") == count
        assert source.count("MISE_EXEC_AUTO_INSTALL: 'false'") == count
    jev = (ROOT / "ansible/jev-fastpath-provider.yml").read_text()
    assert '''- "{{ jev_release }}"''' in jev
    assert "- /usr/bin/env" in jev
