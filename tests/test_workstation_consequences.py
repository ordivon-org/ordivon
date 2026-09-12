from __future__ import annotations

import pathlib
import subprocess


def test_pnpm_first_path_uses_mise_and_project_package_manager() -> None:
    pnpm = pathlib.Path("/root/tools/bin/pnpm")
    assert pnpm.is_symlink(), "pnpm compatibility path is not externally managed"
    assert pnpm.resolve() == pathlib.Path("/usr/bin/mise"), pnpm.resolve()
    config = pathlib.Path("/root/.config/mise/config.toml").read_text()
    assert 'idiomatic_version_file_enable_tools = ["node", "pnpm"]' in config
    expected = {
        "/root/projects/ordivon-game": "10.33.2",
        "/root/projects/ordivon-media": "10.33.2",
        "/root/projects/ordivon-web": "11.17.0",
    }
    for root, version in expected.items():
        cp = subprocess.run(
            [str(pnpm), "--version"], cwd=root, check=False, text=True,
            capture_output=True, timeout=15,
        )
        assert cp.returncode == 0, cp.stderr or cp.stdout
        assert cp.stdout.strip() == version, (root, cp.stdout, cp.stderr)


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


def test_netdata_is_loopback_reachable() -> None:
    active = subprocess.run(
        ["/usr/bin/systemctl", "is-active", "netdata.service"],
        text=True, capture_output=True, timeout=10,
    )
    assert active.returncode == 0 and active.stdout.strip() == "active", active.stderr or active.stdout
    sockets = subprocess.run(
        ["/usr/bin/ss", "-ltnH", "sport", "=", ":19999"],
        text=True, capture_output=True, timeout=10,
    )
    assert sockets.returncode == 0, sockets.stderr
    lines = [line for line in sockets.stdout.splitlines() if line.strip()]
    assert lines and all("127.0.0.1:19999" in line for line in lines), sockets.stdout
    info = subprocess.run(
        ["/usr/bin/curl", "--noproxy", "*", "--fail", "--silent", "--show-error",
         "http://127.0.0.1:19999/api/v1/info"],
        text=True, capture_output=True, timeout=10,
    )
    assert info.returncode == 0, info.stderr or info.stdout

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
