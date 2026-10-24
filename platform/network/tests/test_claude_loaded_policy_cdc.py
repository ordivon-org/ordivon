"""Claude convergence must consume the loaded systemd policy, not just copied files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")


def _task(name: str) -> str:
    return TASKS.split(f"\n  consumer:claude:{name}:\n", 1)[1].split(
        "\n  consumer:", 1
    )[0]


def test_claude_converge_proves_loaded_policy_not_only_transport() -> None:
    converge = _task("converge")
    verify = _task("verify")
    assert "task: consumer:claude:verify" in converge
    assert "task: consumer:claude:ready" not in converge
    for unit in ("network-v2-claude-proxy.service", "network-v2-claude-relay.service"):
        assert (
            f'test "$(systemctl show --value -p PartOf {unit})" = network-v2-claude.target'
            in verify
        )
        assert (
            f'test "$(systemctl show --value -p NeedDaemonReload {unit})" = no'
            in verify
        )
        assert (
            f"cmp -s consumers/claude/systemd/{unit} /etc/systemd/system/{unit}"
            in verify
        )
