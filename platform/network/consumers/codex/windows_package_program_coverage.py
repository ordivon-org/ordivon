#!/usr/bin/env python3
"""One-shot Windows native MSIX process and descendant coverage witness.

Read only: Get-AppxPackage, CIM Win32_Process, Authenticode.
This is not a deployed firewall rule or proof of complete future process scope.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from datetime import datetime
import json
import ntpath
import subprocess
import sys

PS_QUERY = r'''
$ErrorActionPreference = 'Stop'
$pkg = Get-AppxPackage -Name 'OpenAI.Codex' | Sort-Object Version -Descending | Select-Object -First 1
if (-not $pkg) { throw 'PACKAGE_NOT_INSTALLED' }
$ps = @(Get-CimInstance Win32_Process | ForEach-Object {
  @{pid=[int]$_.ProcessId; parentPid=[int]$_.ParentProcessId
    name=[string]$_.Name; executable=[string]$_.ExecutablePath
    session=[int]$_.SessionId
    creationUtc=if ($_.CreationDate) { ([datetime]$_.CreationDate).ToUniversalTime().ToString('o') } else { $null }}
})
$root = [string]$pkg.InstallLocation
$paths = @($ps | Where-Object {
  $_.executable -and $_.executable.StartsWith($root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)
} | ForEach-Object { $_.executable } | Sort-Object -Unique)
$sigs = @($paths | ForEach-Object {
  $s=Get-AuthenticodeSignature -LiteralPath $_ -ErrorAction SilentlyContinue
  @{executable=$_; status=if ($s) {[string]$s.Status} else {'UNKNOWN'}}
})
@{packageFamily=[string]$pkg.PackageFamilyName;packageVersion=[string]$pkg.Version
  installLocation=$root;processes=$ps;signatures=$sigs} | ConvertTo-Json -Depth 7 -Compress
'''


def normalized(value: str) -> str:
    return ntpath.normcase(ntpath.normpath(value)) if value else ""


def in_root(path: str, root: str) -> bool:
    root = normalized(root).rstrip("\\")
    return bool(root and path and normalized(path).startswith(root + "\\"))


def timestamp(value: str | None):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else None
    except (ValueError, TypeError):
        return None


def summarize(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Invalid evidence")
    root = data.get("installLocation", "")
    if not isinstance(root, str) or not ntpath.isabs(root):
        raise ValueError("Missing absolute package installation root")
    rows = data.get("processes")
    sig_rows = data.get("signatures")
    if not isinstance(rows, list) or len(rows) > 20000 or not isinstance(sig_rows, list):
        raise ValueError("Unbounded process/signature input")
    signatures = {normalized(x["executable"]): str(x.get("status", "UNKNOWN"))
                  for x in sig_rows if isinstance(x, dict) and isinstance(x.get("executable"), str)}
    by_pid = {}
    children = defaultdict(list)
    for p in rows:
        if not isinstance(p, dict):
            raise ValueError("Not a CIM process")
        pid, ppid = p.get("pid"), p.get("parentPid")
        if type(pid) is not int or type(ppid) is not int or pid < 0 or ppid < 0:
            raise ValueError("Invalid native process ID")
        if pid in by_pid:
            raise ValueError("Duplicate PID")
        by_pid[pid] = p
        children[ppid].append(p)

    roots = [p for p in rows if in_root(p.get("executable", ""), root)]
    seen = {p["pid"] for p in roots}
    queue = deque(roots)
    external = []
    missing_generation = 0
    reused_pid = 0
    while queue:
        parent = queue.popleft()
        for child in children[parent["pid"]]:
            if child["pid"] in seen:
                continue
            pt, ct = timestamp(parent.get("creationUtc")), timestamp(child.get("creationUtc"))
            if pt is None or ct is None:
                missing_generation += 1
                continue
            if ct < pt:
                reused_pid += 1
                continue
            seen.add(child["pid"])
            queue.append(child)
            if not in_root(child.get("executable", ""), root):
                external.append(child)

    programs = defaultdict(list)
    for p in roots:
        programs[normalized(p["executable"])].append(p)
    observed = []
    for path, members in sorted(programs.items()):
        observed.append({
            "relativePath": ntpath.relpath(path, normalized(root)).replace("\\", "/"),
            "processCount": len(members),
            "signature": signatures.get(path, "UNKNOWN"),
            "sessions": dict(sorted(Counter(str(p.get("session", "UNKNOWN"))
                                               for p in members).items())),
        })
    signed = bool(observed) and all(p["signature"] == "Valid" for p in observed)
    status = ("UNKNOWN" if not roots or missing_generation else
              "EXTERNAL_DESCENDANTS_OBSERVED" if external else
              "NO_EXTERNAL_DESCENDANTS_IN_SNAPSHOT")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network.windows-package-program-coverage",
        "packageFamily": data.get("packageFamily"),
        "packageVersion": data.get("packageVersion"),
        "standing": status,
        "packageProcessCount": len(roots),
        "uniquePackagePrograms": len(observed),
        "allObservedPackageBinariesSigned": signed,
        "packagePrograms": observed,
        "externalDescendantCount": len(external),
        "externalDescendantBasenames": dict(sorted(Counter(
            str(p.get("name") or "UNKNOWN").lower() for p in external).items())),
        "externalDescendantMissingPath": sum(not p.get("executable") for p in external),
        "unknownParentGeneration": missing_generation,
        "reusedParentPidExcluded": reused_pid,
        "allProtocolFirewallCoverage": "UNKNOWN",
        "source": "read-only Microsoft Appx / Win32_Process CIM / Authenticode",
        "unproved": [
            "new/terminated child processes after this snapshot",
            "whether descendants actually generated network traffic",
            "all-protocol Windows Firewall app isolation",
            "package SID-based rule applicability",
            "DNS/DoH/IPv6/UDP/QUIC paths and missing historical ancestors",
        ],
    }


def main() -> int:
    if sys.platform != "win32":
        print(json.dumps({"standing": "UNKNOWN", "reason": "WINDOWS_ONLY"}))
        return 2
    try:
        query = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
                                "-Command", PS_QUERY], capture_output=True,
                               text=True, timeout=40, check=False)
        if query.returncode:
            raise ValueError("Native Windows query failed")
        result = summarize(json.loads(query.stdout))
    except (OSError, ValueError, subprocess.TimeoutExpired, KeyError) as exc:
        print(json.dumps({"standing": "UNKNOWN", "reason": type(exc).__name__}))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["standing"] != "UNKNOWN" and result["allObservedPackageBinariesSigned"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
