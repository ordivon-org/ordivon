#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, os, platform, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "evidence/capability-matrix.json"
CURRENT = ROOT / "evidence/current-capabilities.json"
SOURCE_ROOTS = ["Taskfile.yml", "config", "systemd", "acceptance", "scripts/capability-report.py", "evidence/capability-matrix.json"]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def source_fingerprint() -> str:
    h = hashlib.sha256()
    paths = []
    for item in SOURCE_ROOTS:
        p = ROOT / item
        if p.is_file():
            paths.append(p)
        elif p.is_dir():
            paths.extend(x for x in p.rglob("*") if x.is_file())
    for p in sorted(paths, key=lambda x: x.relative_to(ROOT).as_posix()):
        rel = p.relative_to(ROOT).as_posix()
        mode = oct(p.stat().st_mode & 0o777)
        digest = sha256_bytes(p.read_bytes())
        h.update(f"{rel}\0{mode}\0{digest}\n".encode())
    return "sha256:" + h.hexdigest()

def os_release():
    vals = {}
    p = Path("/etc/os-release")
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                vals[k] = v.strip().strip('"')
    return {"id": vals.get("ID", "unknown"), "versionId": vals.get("VERSION_ID", "unknown")}

def platform_info():
    kernel = platform.release()
    info = {
        "system": platform.system(),
        "architecture": platform.machine(),
        "kernelRelease": kernel,
        "os": os_release(),
        "wsl": "microsoft" in kernel.lower() or bool(os.environ.get("WSL_INTEROP")),
    }
    stable = json.dumps(info, sort_keys=True, separators=(",", ":")).encode()
    return info, "sha256:" + sha256_bytes(stable)

def git_revision():
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"

def build_local_report():
    matrix = json.loads(MATRIX.read_text())
    plat, plat_digest = platform_info()
    local = matrix["localWsl"]
    return {
        "schemaVersion": 2,
        "platform": "current-wsl",
        "standing": local["standing"],
        "authority": {
            "entryPoint": local["entryPoint"],
            "acceptedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "sourceRevision": git_revision(),
            "sourceFingerprint": source_fingerprint(),
            "platformFingerprint": plat_digest
        },
        "platformEvidence": plat,
        "generic": local["capabilities"],
        "externalFidelity": local["externalFidelity"],
        "outsideNetworkBoundary": {
            "windowsHostRebootWslAutolaunch": "WORKSTATION_BOOTSTRAP",
            "consumerCutover": "CONSUMER_MIGRATION",
            "legacyRetirement": "CONSUMER_MIGRATION"
        }
    }

def write_local(path: Path):
    report = build_local_report()
    path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
    print(path)

def verify_local(path: Path):
    report = json.loads(path.read_text())
    _, plat_digest = platform_info()
    failures = []
    expected_source = source_fingerprint()
    if report.get("schemaVersion") != 2: failures.append("schemaVersion")
    if report.get("authority", {}).get("sourceFingerprint") != expected_source: failures.append("sourceFingerprint")
    if report.get("authority", {}).get("platformFingerprint") != plat_digest: failures.append("platformFingerprint")
    if report.get("authority", {}).get("entryPoint") != "task accept:local": failures.append("entryPoint")
    if report.get("standing") != "LOCAL_WSL_GRADUATED": failures.append("standing")
    if failures:
        raise SystemExit("stale/invalid capability report: " + ",".join(failures))
    print("evidence-local-current=PASS")

ap = argparse.ArgumentParser()
ap.add_argument("command", choices=["write-local", "verify-local"])
ap.add_argument("--output", default=str(CURRENT))
a = ap.parse_args()
out = Path(a.output)
if a.command == "write-local": write_local(out)
else: verify_local(out)
