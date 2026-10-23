"""Codex's default PATH command reuses the existing scoped VPN carrier."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "workstation/nix/nix/home.nix"
SOURCE_DOC = ROOT / "workstation/nix/CODEX_DEFAULT_VPN.md"


def test_codex_default_and_raw_have_disjoint_authority() -> None:
    home = HOME.read_text()
    assert 'home.file."tools/bin/codex".source' in home
    assert 'mkOutOfStoreSymlink "/usr/local/bin/codex-vpn"' in home
    assert 'home.file."tools/bin/codex-raw".source' in home
    assert '/root/tools/share/codex-pnpm-${codexVersion}/node_modules/@openai/codex/bin/codex.js' in home
    # A default CLI path that resolves to its own upstream name would
    # recursively launch the VPN wrapper after cutover.
    section = home.split('home.file."tools/bin/codex".source =', 1)[1].split(';', 1)[0]
    assert "codex-pnpm-" not in section
    assert "codex-raw" not in section


def test_codex_vpn_policy_is_owner_native_and_fail_closed() -> None:
    doc = SOURCE_DOC.read_text()
    for required in (
        "/usr/local/bin/codex-vpn",
        "/root/tools/bin/codex-raw",
        "127.0.0.1:19982",
        "network-v2-codex.target",
        "rollback",
        "readiness",
    ):
        assert required in doc
