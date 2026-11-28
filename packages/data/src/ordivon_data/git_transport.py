"""Bounded POSIX pipe observation for Data's local native Git commands.

The caller owns the command contract and output budget. This is not a
general-purpose execution service or a descendant-process containment layer.
"""

from __future__ import annotations

import os
import selectors
import subprocess
import time


def capture_git_output(
    argv: list[str],
    *,
    env: dict[str, str],
    input_bytes: bytes | None,
    max_output: int,
    timeout: float,
) -> bytes:
    """Return only complete, diagnostic-free output within the caller's budget."""
    if max_output < 0 or timeout <= 0:
        raise ValueError("invalid Git transport budget")
    deadline = time.monotonic() + timeout
    output = bytearray()
    data = memoryview(input_bytes or b"")
    offset = 0

    def remaining() -> float:
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(argv, timeout)
        return left

    with (
        selectors.DefaultSelector() as ready,
        subprocess.Popen(
            argv,
            env=env,
            stdin=subprocess.PIPE if data else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        ) as process,
    ):
        try:
            for pipe, label in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                os.set_blocking(pipe.fileno(), False)
                ready.register(pipe, selectors.EVENT_READ, label)
            if data:
                os.set_blocking(process.stdin.fileno(), False)
                ready.register(process.stdin, selectors.EVENT_WRITE, "stdin")
            while ready.get_map():
                for key, _ in ready.select(remaining()):
                    pipe = key.fileobj
                    remaining()
                    if key.data == "stdin":
                        try:
                            offset += os.write(
                                pipe.fileno(), data[offset : offset + 65536]
                            )
                        except BlockingIOError:
                            continue
                        if offset == len(data):
                            ready.unregister(pipe)
                            pipe.close()
                        continue
                    size = (
                        1
                        if key.data == "stderr"
                        else min(65536, max_output - len(output) + 1)
                    )
                    try:
                        chunk = os.read(pipe.fileno(), size)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        ready.unregister(pipe)
                        pipe.close()
                        continue
                    if key.data == "stderr":
                        raise ValueError(
                            "committed ODPS source cannot be resolved: native diagnostic"
                        )
                    if len(chunk) > max_output - len(output):
                        raise ValueError(
                            "Git native output exceeds bounded transport bytes"
                        )
                    output.extend(chunk)
            code = process.wait(timeout=remaining())
            if code:
                raise subprocess.CalledProcessError(code, argv)
            return bytes(output)
        finally:
            # Kill/reap the exact child on error, without draining rejected
            # output into memory. Popen owns the pipe handles.
            if process.poll() is None:
                process.kill()
                process.wait()
