"""TEST-HARNESS-DEEPSEEK-TERMINAL-001: a completed provider request cannot look pending.

No provider, network, secrets, or new execution layer is involved.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import unittest

from ordivon_harness.ordivon.deepseek import _HttpxPostHandle
from ordivon_harness.ordivon.model import (
    AgentTurnAdapterError,
    AgentTurnDispatchSafety,
    AgentTurnFailureCode,
)


def _completed_handle(
    *, response: bytes | None, error: Exception | None = None
) -> _HttpxPostHandle:
    # Model the four possible terminal observations without creating a provider effect.
    handle = object.__new__(_HttpxPostHandle)
    handle._done = threading.Event()
    handle._done.set()
    handle._result = response
    handle._error = error
    return handle


class DeepSeekTerminalStateContract(unittest.TestCase):
    def test_pending_request_remains_pending(self) -> None:
        handle = _completed_handle(response=None)
        handle._done.clear()
        self.assertIsNone(handle.poll(0))

    def test_valid_terminal_response_returns_bytes(self) -> None:
        self.assertEqual(_completed_handle(response=b"ok").poll(0), b"ok")

    def test_terminal_error_is_preserved(self) -> None:
        error = AgentTurnAdapterError("provider failed")
        with self.assertRaises(AgentTurnAdapterError) as caught:
            _completed_handle(response=None, error=error).poll(0)
        self.assertIs(caught.exception, error)

    def test_inconsistent_terminal_state_is_failed_not_pending(self) -> None:
        with self.assertRaisesRegex(AgentTurnAdapterError, "without a response") as caught:
            _completed_handle(response=None).poll(0)
        self.assertEqual(caught.exception.failure_code, AgentTurnFailureCode.FAILED)
        self.assertEqual(
            caught.exception.dispatch_safety, AgentTurnDispatchSafety.DISPATCH_AMBIGUOUS
        )

    def test_optimized_interpreter_cannot_erase_terminal_check(self) -> None:
        script = """
import threading
from ordivon_harness.ordivon.deepseek import _HttpxPostHandle
from ordivon_harness.ordivon.model import AgentTurnAdapterError
h = object.__new__(_HttpxPostHandle)
h._done = threading.Event()
h._done.set()
h._result = None
h._error = None
try:
    h.poll(0)
except AgentTurnAdapterError:
    raise SystemExit(0)
raise SystemExit('optimized Python incorrectly reported a completed effect as pending')
"""
        result = subprocess.run(
            [sys.executable, "-O", "-c", script], capture_output=True, text=True, timeout=15
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
