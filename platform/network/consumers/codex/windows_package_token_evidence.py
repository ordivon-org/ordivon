#!/usr/bin/env python3
"""Read-only Windows MSIX package SID vs live Win32 process token refinement.

Reuses Microsoft Userenv/Advapi32/Kernel32 APIs. No firewall or audit policy
mutation, no token impersonation, no driver or persistent packet capture.
IMPORTANT: Missing AppContainer SIDs in sampled tokens does NOT prove that
NetFirewallRule -Package never matches packaged classic Win32 apps.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import re
import sys

MAX_TARGETS = 32
TARGET_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}\.exe$", re.IGNORECASE)
PACKAGE_FAMILY = re.compile(r"^[A-Za-z0-9_.-]{1,200}_[A-Za-z0-9]{13}$")


def evaluate(package_sid: str | None, results: list[dict]) -> dict:
    """Keep observed process-token membership distinct from WFP enforcement."""
    complete = bool(results) and all(item.get("queryStatus") == "OK" for item in results)
    matches = sum(bool(item.get("packageSidInGroups")
                       or item.get("packageSidEqualsAppContainer")) for item in results)
    absent = complete and matches == 0 and package_sid is not None
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network.windows-packaged-process-token-refinement",
        "tokenObservation": (
            "SAMPLED_PACKAGE_SID_ABSENT" if absent else
            "SAMPLED_PACKAGE_SID_PRESENT" if complete and matches else
            "UNKNOWN"
        ),
        "packageFirewallEnforcement": "UNKNOWN",
        "packageSidDerived": package_sid is not None,
        "sampledProcesses": len(results),
        "fullyReadTokens": complete,
        "matchingTokens": matches,
        "processes": results,
        "limitations": [
            "TokenIsAppContainer and TokenGroups are sampled process attributes",
            "MSIX package registration and actual process token are separate facts",
            "A missing AppContainer SID does not disprove other WFP package classification",
            "No New-NetFirewallRule -Package effectiveness has been measured",
            "No per-process direct/UDP/IPv6/DNS/DoH egress enforcement proof",
        ],
        "sideEffects": "READ_ONLY",
    }


def parse_target(value: str) -> tuple[str, int]:
    if ":" not in value:
        raise ValueError("Target must be basename.exe:PID")
    name, raw_pid = value.rsplit(":", 1)
    if not TARGET_NAME.fullmatch(name) or not raw_pid.isdecimal():
        raise ValueError("Invalid executable name or PID")
    pid = int(raw_pid)
    if not 1 < pid < 2**32:
        raise ValueError("PID outside real process range")
    return name.lower(), pid


def inspect_native(package_family: str, targets: list[tuple[str, int]]) -> dict:
    if sys.platform != "win32":
        raise RuntimeError("Native token inspection requires Windows")
    if not PACKAGE_FAMILY.fullmatch(package_family):
        raise ValueError("Invalid package family name")
    if not targets or len(targets) > MAX_TARGETS:
        raise ValueError("Target count outside bounded read range")

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    env = ctypes.WinDLL("userenv", use_last_error=True)
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    adv.OpenProcessToken.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
    ]
    adv.OpenProcessToken.restype = wintypes.BOOL
    adv.GetTokenInformation.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD)
    ]
    adv.GetTokenInformation.restype = wintypes.BOOL
    adv.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)
    ]
    adv.ConvertSidToStringSidW.restype = wintypes.BOOL
    k32.LocalFree.argtypes = [wintypes.HLOCAL]
    k32.LocalFree.restype = wintypes.HLOCAL
    adv.FreeSid.argtypes = [ctypes.c_void_p]
    adv.FreeSid.restype = ctypes.c_void_p
    env.DeriveAppContainerSidFromAppContainerName.argtypes = [
        wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)
    ]
    env.DeriveAppContainerSidFromAppContainerName.restype = wintypes.HRESULT

    class SidAndAttributes(ctypes.Structure):
        _fields_ = [("sid", ctypes.c_void_p),
                    ("attributes", wintypes.DWORD)]

    class TokenGroups(ctypes.Structure):
        _fields_ = [("count", wintypes.DWORD),
                    ("groups", SidAndAttributes * 1)]

    def sid_to_string(ptr: int | None) -> str | None:
        if not ptr:
            return None
        out = wintypes.LPWSTR()
        if not adv.ConvertSidToStringSidW(ptr, ctypes.byref(out)):
            raise OSError(ctypes.get_last_error(), "ConvertSidToStringSidW")
        try:
            return out.value
        finally:
            k32.LocalFree(ctypes.cast(out, wintypes.HLOCAL))

    derived_ptr = ctypes.c_void_p()
    hr = env.DeriveAppContainerSidFromAppContainerName(
        package_family, ctypes.byref(derived_ptr)
    )
    if hr != 0:
        raise OSError("DeriveAppContainerSidFromAppContainerName failed")
    try:
        derived = sid_to_string(derived_ptr.value)
    finally:
        if derived_ptr.value:
            adv.FreeSid(derived_ptr)

    def get_info(token: wintypes.HANDLE, cls: int) -> ctypes.Array:
        req = wintypes.DWORD(0)
        adv.GetTokenInformation(token, cls, None, 0, ctypes.byref(req))
        if req.value > 1_000_000:
            raise ValueError("Unbounded native token buffer")
        buf = ctypes.create_string_buffer(max(8, req.value))
        if not adv.GetTokenInformation(token, cls, buf, len(buf),
                                       ctypes.byref(req)):
            raise OSError(ctypes.get_last_error(), "GetTokenInformation")
        return buf

    observations = []
    for name, pid in targets:
        item = {"process": name, "queryStatus": "UNKNOWN"}
        process = k32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not process:
            item["queryStatus"] = "PROCESS_UNAVAILABLE"
            observations.append(item)
            continue
        try:
            token = wintypes.HANDLE()
            if not adv.OpenProcessToken(process, 0x0008, ctypes.byref(token)):
                item["queryStatus"] = "TOKEN_UNAVAILABLE"
                observations.append(item)
                continue
            try:
                app_container = ctypes.cast(
                    get_info(token, 29), ctypes.POINTER(wintypes.DWORD)
                ).contents.value
                sid_info = get_info(token, 31)
                actual_sid_ptr = ctypes.cast(
                    sid_info, ctypes.POINTER(ctypes.c_void_p)
                ).contents.value
                actual_sid = sid_to_string(actual_sid_ptr)
                groups = get_info(token, 2)
                count = ctypes.cast(
                    groups, ctypes.POINTER(wintypes.DWORD)
                ).contents.value
                if count > 1000:
                    raise ValueError("Unexpected token group cardinality")
                base = ctypes.addressof(groups) + TokenGroups.groups.offset
                has_group = False
                for i in range(count):
                    entry = SidAndAttributes.from_address(
                        base + i * ctypes.sizeof(SidAndAttributes)
                    )
                    if sid_to_string(entry.sid) == derived:
                        has_group = True
                        break
                item.update({
                    "queryStatus": "OK",
                    "isAppContainer": bool(app_container),
                    "tokenHasAppContainerSid": actual_sid is not None,
                    "packageSidEqualsAppContainer": derived == actual_sid,
                    "packageSidInGroups": has_group,
                })
            except (OSError, ValueError, TypeError):
                item["queryStatus"] = "TOKEN_READ_ERROR"
            finally:
                k32.CloseHandle(token)
        finally:
            k32.CloseHandle(process)
        observations.append(item)
    return evaluate(derived, observations)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package-family", required=True)
    ap.add_argument("--target", action="append", required=True)
    ns = ap.parse_args()
    try:
        samples = [parse_target(item) for item in ns.target]
        result = inspect_native(ns.package_family, samples)
    except (RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"kind": "ordivon.network.windows-packaged-process-token-refinement",
                          "tokenObservation": "UNKNOWN",
                          "packageFirewallEnforcement": "UNKNOWN",
                          "failure": type(exc).__name__,
                          "sideEffects": "READ_ONLY"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["fullyReadTokens"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
