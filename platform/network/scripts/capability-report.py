#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, os, platform, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "evidence/capability-matrix.json"
CURRENT = ROOT / "evidence/current-capabilities.json"
SOURCE_ROOTS = ["Taskfile.yml", "config", "systemd", "acceptance", "scripts/capability-report.py", "evidence/capability-matrix.json"]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def source_fingerprint() -> str:
    """Fingerprint tracked behavior inputs using Git mode plus current tracked bytes.

    Git mode is the source semantic (100644/100755), not the filesystem mode chosen by
    a worktree creator or umask. Current bytes are read from the worktree so tracked
    dirty content still invalidates evidence. Untracked/generated files are excluded.
    """
    h = hashlib.sha256()
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", *SOURCE_ROOTS]
    )
    rels = [x.decode() for x in raw.split(b"\0") if x]
    for rel in sorted(rels):
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"tracked source input missing or not a regular file: {rel}")
        stage = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files", "-s", "--", rel], text=True
        ).strip()
        if not stage:
            raise RuntimeError(f"tracked source input missing from index: {rel}")
        mode = stage.split()[0]
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
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        members: dict[str, object] = {}
        for name, value in pairs:
            if name in members:
                raise ValueError(f"duplicate JSON member: {name}")
            members[name] = value
        return members

    report = json.loads(path.read_text(), object_pairs_hook=unique_object)
    expected = build_local_report()
    failures = []
    # This is a closed evidence projection, not a bag of optional claims.
    # Unknown fields are not authenticated by sourceFingerprint and cannot
    # silently become an authority signal for a downstream consumer.
    if type(report) is not dict:
        raise SystemExit("stale/invalid capability report: reportSchema")
    if set(report) != set(expected):
        failures.append("reportSchema")
    authority = report.get("authority") if type(report) is dict else None
    if type(authority) is not dict:
        raise SystemExit("stale/invalid capability report: authoritySchema")
    if set(authority) != set(expected["authority"]):
        failures.append("authoritySchema")

    accepted_at = authority.get("acceptedAt")
    # The historical timestamp is informational; it is not a freshness
    # certificate. Check producer-compatible UTC shape, not an invented TTL.
    if type(accepted_at) is not str or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00", accepted_at
    ) is None:
        failures.append("acceptedAt")
    else:
        try:
            dt.datetime.fromisoformat(accepted_at)
        except ValueError:
            failures.append("acceptedAt")
    expected_source = expected["authority"]["sourceFingerprint"]
    plat_digest = expected["authority"]["platformFingerprint"]
    if type(report.get("schemaVersion")) is not int or report["schemaVersion"] != 2: failures.append("schemaVersion")
    # The source digest authenticates the matrix, not arbitrary fields in the
    # materialized report. Verify the actual declared capabilities and scope.
    # Byte-stable JSON comparison distinguishes true from 1 and 2 from 2.0.
    for field in ("platform", "platformEvidence", "generic", "externalFidelity", "outsideNetworkBoundary"):
        if json.dumps(report.get(field), sort_keys=True) != json.dumps(expected[field], sort_keys=True):
            failures.append(field)
    # A matching tree fingerprint does not prove the reported Git SourceCut:
    # two commits can have the same Network bytes, and this field is material
    # provenance. Never admit UNKNOWN when Git cannot qualify its revision.
    actual_revision = report.get("authority", {}).get("sourceRevision")
    expected_revision = expected["authority"]["sourceRevision"]
    if expected_revision == "UNKNOWN" or type(actual_revision) is not str or actual_revision != expected_revision:
        failures.append("sourceRevision")
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
