"""Owner-native regression: common upstream loss cannot multiply time budgets."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("consumer", ("supply-chain",))
def test_multi_origin_readiness_stops_retrying_when_shared_deadline_expires(
    tmp_path: Path, consumer: str
) -> None:
    """Advance Bash's builtin monotonic SECONDS after one failed attempt.

    No wallclock waiting, external network, VPN mutation or credentials.
    This red/green fixture checks actual Bash loop behavior, not a comment.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    attempts = tmp_path / "attempts"
    bash_env = tmp_path / "injected-clock.sh"
    bash_env.write_text(
        "sleep() { SECONDS=$((SECONDS + 1000)); }\n", encoding="utf-8"
    )
    executables = {
        "systemctl": "#!/bin/sh\nexit 0\n",
        "ss": (
            "#!/bin/sh\nprintf 'LISTEN 127.0.0.1:19881\n"
            "LISTEN 127.0.0.1:19581\n'\n"
        ),
        "curl": (
            "#!/bin/sh\nprintf 'attempt\n' >> \"$BUDGET_ATTEMPTS\"\n"
            "printf '000 000'\nexit 7\n"
        ),
    }
    for name, content in executables.items():
        path = bin_dir / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)
    result = subprocess.run(
        ["/usr/bin/bash", str(ROOT / "consumers" / consumer / "ready.sh")],
        env={
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "BASH_ENV": str(bash_env),
            "BUDGET_ATTEMPTS": str(attempts),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert attempts.read_text().splitlines() == ["attempt"], (
        consumer, attempts.read_text(), result.stderr[-500:]
    )


@pytest.mark.parametrize("consumer", ("claude", "chat-ingress"))
def test_namespace_and_chat_readiness_share_one_deadline(
    tmp_path: Path, consumer: str
) -> None:
    """A failed proxy cannot multiply requests after the shared deadline.

    Inject a clock advance through Bash itself; no real network or VPN effects.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    attempts = tmp_path / "attempts"
    bash_env = tmp_path / "advance-clock.sh"
    bash_env.write_text(
        "sleep() { SECONDS=$((SECONDS + 1000)); }\n", encoding="utf-8"
    )
    scripts = {
        "systemctl": "#!/bin/sh\nexit 0\n",
        "ss": "#!/bin/sh\nprintf '127.0.0.1:19481 127.0.0.1:19081\n'\n",
        "curl": (
            "#!/bin/sh\nprintf 'attempt\n' >> \"$BUDGET_ATTEMPTS\"\n"
            "printf '000 000'\nexit 7\n"
        ),
        "ip": (
            "#!/bin/sh\n"
            "if [ \"$1\" = netns ] && [ \"$2\" = exec ]; then\n"
            "  shift 3\n"
            "  case \"$1\" in\n"
            "    ss) printf '10.252.247.1:19482\n'; exit 0;;\n"
            "    ip) exit 0;;\n"
            "    curl) shift; exec curl \"$@\";;\n"
            "  esac\n"
            "fi\nexit 65\n"
        ),
    }
    for name, source in scripts.items():
        target = bin_dir / name
        target.write_text(source, encoding="utf-8")
        target.chmod(0o755)
    result = subprocess.run(
        ["/usr/bin/bash", str(ROOT / "consumers" / consumer / "ready.sh")],
        env={
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "BASH_ENV": str(bash_env),
            "BUDGET_ATTEMPTS": str(attempts),
        },
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )
    assert result.returncode != 0, consumer
    assert result.stdout == ""
    # Claude first proves direct networking cannot bypass the proxy.
    # That separate fail-closed check remains mandatory.
    expected = 2 if consumer == "claude" else 1
    observed = attempts.read_text().splitlines()
    assert len(observed) == expected, (
        consumer, observed, result.stderr[-500:]
    )
