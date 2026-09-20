from __future__ import annotations

import json
import pathlib
import subprocess
import tomllib


def test_pnpm_first_path_uses_mise_and_project_package_manager() -> None:
    pnpm = pathlib.Path("/root/tools/bin/pnpm")
    assert pnpm.is_symlink(), "pnpm compatibility path is not externally managed"
    assert pnpm.resolve() == pathlib.Path("/usr/bin/mise"), pnpm.resolve()
    config = pathlib.Path("/root/.config/mise/config.toml").read_text()
    assert 'idiomatic_version_file_enable_tools = ["node", "pnpm"]' in config

    for root_text in (
        "/root/projects/ordivon-game",
        "/root/projects/ordivon-media",
    ):
        root = pathlib.Path(root_text)
        package = json.loads((root / "package.json").read_text())
        package_manager = package.get("packageManager")
        assert isinstance(package_manager, str) and package_manager.startswith("pnpm@"), (
            root_text,
            package_manager,
        )
        declared_version = package_manager.removeprefix("pnpm@")

        mise_path = root / "mise.toml"
        if not mise_path.is_file():
            mise_path = root / ".mise.toml"
        mise = tomllib.loads(mise_path.read_text())
        assert mise["tools"]["pnpm"] == declared_version, (
            root_text,
            mise["tools"]["pnpm"],
            declared_version,
        )

        cp = subprocess.run(
            [str(pnpm), "--version"], cwd=root, check=False, text=True,
            capture_output=True, timeout=15,
        )
        assert cp.returncode == 0, cp.stderr or cp.stdout
        assert cp.stdout.strip() == declared_version, (root_text, cp.stdout, cp.stderr)


def test_bash_login_and_nonlogin_match_home_manager_policy() -> None:
    expected_path = "/root/tools/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/lib/wsl/lib:/root/.local/bin:/root/bin"
    probe = r"""printf 'PATH=%s\nEDITOR=%s\nVISUAL=%s\nPROJECTS=%s\nHISTFILE=%s\nHISTSIZE=%s\nHISTFILESIZE=%s\nHISTCONTROL=%s\nNOFILE=%s\nCDF=%s\nFF=%s\nFP=%s\n' "$PATH" "$EDITOR" "$VISUAL" "$PROJECTS" "$HISTFILE" "$HISTSIZE" "$HISTFILESIZE" "$HISTCONTROL" "$(ulimit -Sn)" "$(type -t cdf)" "$(type -t ff)" "$(type -t fp)" """
    modes = [
        ["/usr/bin/bash", "--noprofile", "--rcfile", "/root/.bashrc", "-i", "-c", probe],
        ["/usr/bin/bash", "-l", "-i", "-c", probe],
    ]
    for command in modes:
        cp = subprocess.run(
            command, check=False, text=True, capture_output=True, timeout=20,
            env={"HOME": "/root", "USER": "root", "PATH": "/usr/bin:/bin"},
        )
        assert cp.returncode == 0, cp.stderr or cp.stdout
        values = dict(line.split("=", 1) for line in cp.stdout.splitlines() if "=" in line)
        assert values["PATH"] == expected_path
        assert values["EDITOR"] == "vim"
        assert values["VISUAL"] == "vim"
        assert values["PROJECTS"] == "/root/projects"
        assert values["HISTFILE"] == "/dev/null"
        assert values["HISTSIZE"] == "500"
        assert values["HISTFILESIZE"] == "0"
        assert values["HISTCONTROL"] == "ignoreboth:erasedups"
        assert int(values["NOFILE"]) >= 65536
        assert values["CDF"] == values["FF"] == values["FP"] == "function"


def test_default_workstation_observability_services_remain_cold() -> None:
    for service in (
        "netdata.service",
        "prometheus.service",
        "prometheus-node-exporter.service",
        "ordivon-gatus.service",
    ):
        active = subprocess.run(
            ["/usr/bin/systemctl", "is-active", service],
            text=True, capture_output=True, timeout=10,
        )
        enabled = subprocess.run(
            ["/usr/bin/systemctl", "is-enabled", service],
            text=True, capture_output=True, timeout=10,
        )
        assert active.stdout.strip() == "inactive", (service, active.stdout, active.stderr)
        assert enabled.stdout.strip() == "disabled", (service, enabled.stdout, enabled.stderr)

    netdata_socket = subprocess.run(
        ["/usr/bin/ss", "-ltnH", "sport", "=", ":19999"],
        text=True, capture_output=True, timeout=10,
    )
    assert netdata_socket.returncode == 0, netdata_socket.stderr
    assert not netdata_socket.stdout.strip(), netdata_socket.stdout

def _osquery(query: str) -> list[dict[str, str]]:
    import json
    cp = subprocess.run(["/usr/bin/osqueryi", "--json", query], text=True, capture_output=True, timeout=20)
    assert cp.returncode == 0, cp.stderr or cp.stdout
    rows = json.loads(cp.stdout)
    assert rows
    return rows


def test_osquery_is_generic_host_inventory_authority() -> None:
    root = pathlib.Path(__file__).resolve().parents[1] / "inventory" / "queries"
    system = _osquery((root / "system_identity.sql").read_text().strip())[0]
    operating_system = _osquery((root / "os_version.sql").read_text().strip())[0]
    uptime = _osquery((root / "uptime.sql").read_text().strip())[0]
    assert system["hostname"]
    assert int(system["physical_memory"]) > 0
    assert operating_system["platform"] == "arch"
    assert int(uptime["total_seconds"]) >= 0
