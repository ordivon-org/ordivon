#!/usr/bin/env python3
"""Check CVE-2026-3219 status — whether a fixed pip version exists.

Part of DEP-AUDIT-PIP-CVE-2026-3219 debt review mechanism.
When this script reports "FIXED", remove --ignore-vuln CVE-2026-3219
from .github/workflows/security.yml and close the debt record.

Usage:
    python scripts/check_cve_2026_3219.py
    python scripts/check_cve_2026_3219.py --json   # machine-readable output
"""

import json
import sys
import urllib.request
import urllib.error

CVE_ID = "CVE-2026-3219"
OSV_URL = f"https://api.osv.dev/v1/vulns/{CVE_ID}"
DEBT_ID = "DEP-AUDIT-PIP-CVE-2026-3219"
CI_FILE = ".github/workflows/security.yml"
DEBT_FILE = "docs/governance/dependency-audit-debts.jsonl"


def fetch_osv(cve_id: str) -> dict:
    """Fetch vulnerability data from OSV API."""
    url = f"https://api.osv.dev/v1/vulns/{cve_id}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "cve": cve_id}
    except Exception as e:
        return {"error": str(e), "cve": cve_id}


def check_fixed(osv_data: dict) -> dict:
    """Check if a fixed version exists for pip."""
    result = {
        "cve": CVE_ID,
        "debt_id": DEBT_ID,
        "status": "UNKNOWN",
        "fixed_versions": [],
        "action_required": None,
    }

    if "error" in osv_data:
        result["status"] = "FETCH_ERROR"
        result["error"] = osv_data["error"]
        return result

    affected = osv_data.get("affected", [])
    for entry in affected:
        pkg = entry.get("package", {}).get("name", "")
        if "pip" not in pkg.lower():
            continue

        ranges = entry.get("ranges", [])
        for r in ranges:
            if r.get("type") == "ECOSYSTEM":
                events = r.get("events", [])
                for event in events:
                    if "fixed" in event:
                        result["fixed_versions"].append(event["fixed"])

    if result["fixed_versions"]:
        result["status"] = "FIXED"
        result["action_required"] = (
            f"Fixed version(s) available: {result['fixed_versions']}. "
            f"Remove --ignore-vuln {CVE_ID} from {CI_FILE} "
            f"and close debt {DEBT_ID} in {DEBT_FILE}."
        )
    else:
        result["status"] = "NO_FIX_UPSTREAM"
        result["action_required"] = (
            f"No fixed version yet. Keep --ignore-vuln {CVE_ID} in CI. "
            f"Re-check weekly."
        )

    return result


def check_ci_ignore_present() -> bool:
    """Verify the CI file still has the ignore directive."""
    try:
        with open(CI_FILE) as f:
            content = f.read()
        return f"--ignore-vuln {CVE_ID}" in content
    except FileNotFoundError:
        return False


def main():
    as_json = "--json" in sys.argv

    osv_data = fetch_osv(CVE_ID)
    result = check_fixed(osv_data)
    result["ci_ignore_present"] = check_ci_ignore_present()

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"CVE:     {result['cve']}")
        print(f"Debt:    {result['debt_id']}")
        print(f"Status:  {result['status']}")
        print(f"Fixed:   {result['fixed_versions'] or 'None'}")
        print(f"CI gate: {'ACTIVE' if result['ci_ignore_present'] else 'MISSING'}")
        print(f"Action:  {result['action_required']}")

    # Exit 0 = no action needed or fixed; exit 2 = still needs ignore
    if result["status"] == "FIXED":
        return 0
    return 0  # NO_FIX_UPSTREAM is expected, not an error


if __name__ == "__main__":
    sys.exit(main())
