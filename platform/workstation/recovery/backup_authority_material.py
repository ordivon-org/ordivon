#!/usr/bin/env python3
"""Create and verify an encrypted off-VHD recovery bundle for workstation authority material."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = tomllib.loads(Path(__file__).with_name("recovery.toml").read_text())
REC = CFG["recovery"]
AGE_KEY = Path("/root/.config/sops/age/keys.txt")
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def decode_windows_diagnostic(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def run_windows_powershell_json(script: str) -> dict[str, object]:
    utf8_prefix = (
        '$utf8=[Text.UTF8Encoding]::new($false); '
        '[Console]::OutputEncoding=$utf8; '
        '$OutputEncoding=$utf8; '
    )
    proc = subprocess.run(
        [POWERSHELL, "-NoProfile", "-Command", utf8_prefix + script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stderr = decode_windows_diagnostic(proc.stderr).strip()
    if proc.returncode != 0:
        detail = stderr or "no stderr"
        raise RuntimeError(f"Windows PowerShell failed ({proc.returncode}): {detail}")
    try:
        stdout = proc.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("Windows PowerShell protocol output was not UTF-8") from error
    try:
        value = json.loads(stdout.strip())
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Windows PowerShell protocol returned invalid JSON: {stdout!r}; stderr={stderr!r}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"Windows PowerShell protocol returned non-object JSON: {value!r}")
    return value


def windows_path(path: Path) -> str:
    parts = path.parts
    if len(parts) < 4 or parts[1] != "mnt" or len(parts[2]) != 1:
        raise ValueError(f"not a drvfs path: {path}")
    drive = parts[2].upper()
    return drive + ":\\" + "\\".join(parts[3:])


def authority_paths() -> list[str]:
    paths = list(REC["authority_paths"])
    for app in CFG.get("external_apps", {}).values():
        paths.extend(app.get("recovery_paths", []))
    return list(dict.fromkeys(paths))


def age_recipient() -> str:
    proc = subprocess.run(
        ["/usr/bin/age-keygen", "-y", str(AGE_KEY)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    value = proc.stdout.strip()
    if not value.startswith("age1"):
        raise RuntimeError("age recipient derivation failed")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def dpapi_receipt_path(outdir: Path) -> Path:
    return outdir / str(REC["dpapi_receipt"])


def reusable_dpapi_receipt(outdir: Path, recipient: str) -> dict[str, object] | None:
    blob = outdir / str(REC["dpapi_blob"])
    restore = outdir / str(REC["dpapi_recovery_script"])
    receipt_path = dpapi_receipt_path(outdir)
    if not (blob.is_file() and restore.is_file() and receipt_path.is_file()):
        return None
    try:
        receipt = json.loads(receipt_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(receipt, dict) or receipt.get("schemaVersion") != 1:
        return None
    if receipt.get("kind") != "ordivon.workstation.age-key-dpapi-binding":
        return None
    if receipt.get("recipient") != recipient:
        return None
    if receipt.get("blobSha256") != sha256_file(blob):
        return None
    if receipt.get("restoreScriptSha256") != sha256_file(restore):
        return None
    if receipt.get("verificationBasis") not in {"windows-dpapi-roundtrip", "legacy-successor-bootstrap"}:
        return None
    return receipt


def write_dpapi_receipt(outdir: Path, recipient: str, *, verification_basis: str, evidence: dict[str, object] | None = None) -> dict[str, object]:
    blob = outdir / str(REC["dpapi_blob"])
    restore = outdir / str(REC["dpapi_recovery_script"])
    receipt_path = dpapi_receipt_path(outdir)
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.age-key-dpapi-binding",
        "recipient": recipient,
        "blobSha256": sha256_file(blob),
        "restoreScriptSha256": sha256_file(restore),
        "verificationBasis": verification_basis,
        "recordedAt": dt.datetime.now(dt.UTC).isoformat(),
        "evidence": evidence or {},
    }
    temporary = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, receipt_path)
    return receipt


def build_tar(target: Path) -> list[str]:
    names: list[str] = []
    with tarfile.open(target, "w") as archive:
        for relative in authority_paths():
            source = Path("/") / relative
            if not source.exists():
                raise FileNotFoundError(source)
            archive.add(source, arcname=relative, recursive=True)
            names.append(relative)
    os.chmod(target, 0o600)
    return names


def verify_age_bundle(bundle: Path) -> int:
    proc = subprocess.Popen(
        ["/usr/bin/age", "-d", "-i", str(AGE_KEY), str(bundle)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    count = 0
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
            for _ in archive:
                count += 1
    finally:
        proc.stdout.close()
    stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"age verification failed: {stderr.strip()}")
    return count


def seal_age_key_dpapi(outdir: Path, recipient: str) -> dict[str, object]:
    reusable = reusable_dpapi_receipt(outdir, recipient)
    if reusable is not None:
        return {"ok": True, "reused": True, "verificationBasis": reusable["verificationBasis"], "receipt": str(dpapi_receipt_path(outdir))}
    win_dir = windows_path(outdir)
    unc_key = r"\\wsl.localhost\archlinux\root\.config\sops\age\keys.txt"
    script = rf'''
$ErrorActionPreference="Stop"
$src="{unc_key}"
$dir="{win_dir}"
$out=Join-Path $dir "{REC['dpapi_blob']}"
$restore=Join-Path $dir "{REC['dpapi_recovery_script']}"
Add-Type -AssemblyName System.Security
$user="${{env:USERDOMAIN}}\${{env:USERNAME}}"
function Assert-RestrictedAcl([string]$Path,[string]$User) {{
  $actual=Get-Acl -LiteralPath $Path
  if(-not $actual.AreAccessRulesProtected){{ throw "DPAPI blob ACL inheritance is not protected" }}
  $rules=@($actual.Access)
  if($rules.Count -ne 2){{ throw "DPAPI blob ACL rule count mismatch: $($rules.Count)" }}
  foreach($identity in @($User,"NT AUTHORITY\SYSTEM")){{
    $matches=@($rules | Where-Object {{ $_.IdentityReference.Value -ieq $identity }})
    if($matches.Count -ne 1){{ throw "DPAPI blob ACL missing exact identity: $identity" }}
    $rule=$matches[0]
    if($rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or $rule.FileSystemRights -ne [Security.AccessControl.FileSystemRights]::FullControl -or $rule.IsInherited){{
      throw "DPAPI blob ACL rule mismatch: $identity"
    }}
  }}
}}
$blobExists=Test-Path -LiteralPath $out
if($blobExists){{ Assert-RestrictedAcl $out $user }}
$plain=[IO.File]::ReadAllBytes($src)
$protected=[Security.Cryptography.ProtectedData]::Protect($plain,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
[IO.File]::WriteAllBytes($out,$protected)
if(-not $blobExists){{
  $acl=New-Object System.Security.AccessControl.FileSecurity
  $acl.SetAccessRuleProtection($true,$false)
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($user,"FullControl","Allow")))
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\SYSTEM","FullControl","Allow")))
  Set-Acl -LiteralPath $out -AclObject $acl
}}
Assert-RestrictedAcl $out $user
$round=[Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($out),$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
$sha=[Security.Cryptography.SHA256]::Create(); $a=([BitConverter]::ToString($sha.ComputeHash($plain))).Replace("-",""); $sha.Dispose()
$sha=[Security.Cryptography.SHA256]::Create(); $b=([BitConverter]::ToString($sha.ComputeHash($round))).Replace("-",""); $sha.Dispose()
if($a -ne $b){{ throw "DPAPI round-trip mismatch" }}
$body=@"
param([Parameter(Mandatory=`$true)][string]`$OutputPath)
`$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Security
`$blob = [IO.File]::ReadAllBytes((Join-Path `$PSScriptRoot "{REC['dpapi_blob']}"))
`$plain = [Security.Cryptography.ProtectedData]::Unprotect(`$blob, `$null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
[IO.File]::WriteAllBytes(`$OutputPath, `$plain)
"@
[IO.File]::WriteAllText($restore,$body,[Text.UTF8Encoding]::new($false))
@{{ok=$true;blobBytes=(Get-Item $out).Length;user=$user;aclVerified=$true;blobPreviouslyExisted=$blobExists}} | ConvertTo-Json -Compress
'''
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            result = run_windows_powershell_json(script)
            receipt = write_dpapi_receipt(
                outdir, recipient, verification_basis="windows-dpapi-roundtrip",
                evidence={"attempt": attempt},
            )
            return {**result, "reused": False, "verificationBasis": receipt["verificationBasis"], "receipt": str(dpapi_receipt_path(outdir))}
        except Exception as error:
            last_error = error
            if attempt < 3:
                time.sleep(1.0 * attempt)
    assert last_error is not None
    raise last_error


def prune(outdir: Path) -> list[str]:
    retain = int(REC["retain_bundles"])
    bundles = sorted(outdir.glob(REC["authority_bundle_glob"]), key=lambda p: p.stat().st_mtime, reverse=True)
    removed: list[str] = []
    for bundle in bundles[retain:]:
        manifest = bundle.with_suffix("").with_suffix(".manifest.txt")
        bundle.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        removed.append(bundle.name)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    outdir = Path(REC["authority_dir"])
    paths = authority_paths()
    missing = [str(Path("/") / p) for p in paths if not (Path("/") / p).exists()]
    plan = {
        "schemaVersion": 1,
        "authorityDir": str(outdir),
        "paths": paths,
        "missing": missing,
        "applyRequested": args.apply,
    }
    if not args.apply:
        print(json.dumps(plan, indent=2))
        return 0 if not missing else 2
    if missing:
        print(json.dumps(plan, indent=2))
        return 2

    outdir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    bundle = outdir / f"ordivon-authority-{stamp}.tar.age"
    manifest = outdir / f"ordivon-authority-{stamp}.manifest.txt"
    recipient = age_recipient()

    with tempfile.TemporaryDirectory(prefix="ordivon-authority-", dir="/tmp") as tmpdir:
        tar_path = Path(tmpdir) / "authority.tar"
        roots = build_tar(tar_path)
        subprocess.run(
            ["/usr/bin/age", "-r", recipient, "-o", str(bundle), str(tar_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
        )

    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    entries = verify_age_bundle(bundle)
    manifest.write_text(
        "\n".join([
            "schemaVersion=1",
            f"createdUtc={stamp}",
            "cipher=age-x25519",
            f"recipient={recipient}",
            f"sha256={digest}",
            f"bundle={bundle.name}",
            "paths=" + " ".join(roots),
            "",
        ])
    )
    dpapi = seal_age_key_dpapi(outdir, recipient)
    removed = prune(outdir)
    report = {
        **plan,
        "status": "completed",
        "bundle": bundle.name,
        "sha256": digest,
        "archiveEntries": entries,
        "dpapi": dpapi,
        "pruned": removed,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
