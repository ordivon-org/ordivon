"""Fail-closed, read-only Windows foreground check for Room Action Kit.

Exit 0 only if the expected executable owns the current foreground window.
Exit 20 for HOLD. Never focuses, unlocks, clicks or sends keyboard input.
"""

import argparse
import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path


def foreground_process_image() -> tuple[int, int, str | None]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    window = user32.GetForegroundWindow()
    if not window:
        return 0, 0, None
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
    # PROCESS_QUERY_LIMITED_INFORMATION, not an input/elevation capability.
    handle = kernel32.OpenProcess(0x1000, False, pid.value)
    if not handle:
        return window, pid.value, None
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(buffer))
        if not kernel32.QueryFullProcessImageNameW(
            handle, 0, buffer, ctypes.byref(length)
        ):
            return window, pid.value, None
        return window, pid.value, buffer.value
    finally:
        kernel32.CloseHandle(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expected_executable", type=Path)
    args = parser.parse_args()
    if sys.platform != "win32":
        print("HOLD: native foreground check requires Windows", file=sys.stderr)
        return 20
    expected = os.path.normcase(os.path.abspath(args.expected_executable))
    if not os.path.isfile(expected):
        print("HOLD: expected native executable does not exist", file=sys.stderr)
        return 20

    hwnd, pid, image = foreground_process_image()
    actual = os.path.normcase(os.path.abspath(image)) if image else None
    owner = Path(image).name if image else "unknown"
    if actual == expected and hwnd:
        print(f"PASS: exact game executable owns foreground; pid={pid} hwnd={hwnd}")
        return 0
    print(f"HOLD: foreground={owner}, pid={pid}, hwnd={hwnd}; no input permitted")
    return 20


if __name__ == "__main__":
    raise SystemExit(main())
