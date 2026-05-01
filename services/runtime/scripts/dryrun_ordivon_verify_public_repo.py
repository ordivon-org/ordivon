#!/usr/bin/env python3
"""Ordivon Verify — Local Public Repo Dry-run (PV-N7).

Creates a local-only public-repo-shaped extraction of Ordivon Verify
from the private repo, using the file manifest. No remote repo creation.
No publish. No license activation.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "product" / "ordivon-verify-public-repo-file-manifest.json"
DEFAULT_OUTPUT = ROOT / ".tmp" / "ordivon-verify-public-repo-dryrun"


def load_manifest() -> list[dict]:
    with open(MANIFEST_PATH) as f:
        data = json.load(f)
    return data.get("entries", [])


def create_dryrun(output_dir: Path, keep: bool = False) -> dict:
    """Create public repo dry-run. Returns result dict."""
    if output_dir.exists() and not keep:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = load_manifest()
    copied = []
    excluded = []
    missing_required = []

    for e in entries:
        source = ROOT / e["source"]
        target = output_dir / (e["target"] or "")
        if e.get("include", False) and e.get("target"):
            if not source.exists():
                if e.get("required", False):
                    missing_required.append(e["source"])
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)
            copied.append(e["source"])
        else:
            excluded.append({"source": e["source"], "reason": e.get("reason", "")})

    # ── Generate public README ──────────────────────────────────────
    readme_path = output_dir / "README.md"
    readme_path.write_text("""# Ordivon Verify

> **v0 prototype.** Not a public release. Not production-ready.
> READY is evidence, not authorization.

Ordivon Verify checks whether AI/agent work can be trusted. It validates
receipts, debt, gates, and documents — locally, read-only, with no API keys
or network access required.

## Quickstart

```bash
pip install ordivon-verify  # not yet available — local prototype
ordivon-verify all
```

Or run the quickstart example:

```bash
ordivon-verify all --root examples/quickstart --config examples/quickstart/ordivon.verify.json
```

## Status Semantics

| Status | Meaning |
|--------|---------|
| READY | Selected checks passed. Evidence, not authorization. |
| BLOCKED | Hard failure detected. Do not claim complete. |
| DEGRADED | Governance incomplete. Review needed. |

## License

Apache-2.0 (proposed, not yet activated).

This is a local dry-run extraction for testing. Not a published package.
""")
    copied.append("README.md (generated)")

    # ── Generate minimal pyproject.toml ─────────────────────────────
    ppt = output_dir / "pyproject.toml"
    ppt.write_text("""[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ordivon-verify"
version = "0.1.0"
description = "Ordivon Verify — AI work verification CLI (prototype)"
requires-python = ">=3.11"

[project.scripts]
ordivon-verify = "ordivon_verify.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
""")
    copied.append("pyproject.toml (generated)")

    # ── Private reference scan on output ────────────────────────────
    import re

    forbidden = [
        r"API_KEY",
        r"SECRET",
        r"TOKEN",
        r"PASSWORD",
        r"Alpaca",
        r"broker",
        r"live.trading",
        r"/root/projects",
        r"PFIOS",
        r"pfios",
        r"AegisOS",
        r"CAIOS",
        r"production-ready",
        r"public.alpha",
        r"published(?!.*not)",
    ]
    findings = []
    for f in sorted(output_dir.rglob("*")):
        if not f.is_file() or f.suffix not in (".py", ".md", ".json", ".jsonl", ".toml"):
            continue
        try:
            content = f.read_text()
        except Exception:
            continue
        for pat in forbidden:
            matches = list(re.finditer(pat, content, re.IGNORECASE))
            for m in matches:
                line = content[: m.start()].count("\n") + 1
                findings.append({
                    "file": str(f.relative_to(output_dir)),
                    "line": line,
                    "match": m.group(0),
                })

    return {
        "output_path": str(output_dir),
        "copied_files": len(copied),
        "excluded_entries": len(excluded),
        "missing_required": missing_required,
        "private_scan_findings": len(findings),
        "private_scan_blocking": len([f for f in findings if not _is_safe(f)]),
        "copied": copied,
        "excluded": excluded,
        "scan_findings": findings,
        "disclaimer": "Local dry-run only. Not a real public repo.",
    }


def _is_safe(finding: dict) -> bool:  # noqa: ARG001
    """Simple safe-context check for scan findings.
    Trust the pre-flight audit for detailed classification.
    Structural pass — flag for manual review."""
    return False


def main(json_output: bool = False) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Ordivon Verify public repo dry-run")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output)
    result = create_dryrun(output_dir, keep=args.keep)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 60)
        print("ORDIVON VERIFY — PUBLIC REPO DRY-RUN")
        print("=" * 60)
        print(f"  Output:              {result['output_path']}")
        print(f"  Copied files/dirs:   {result['copied_files']}")
        print(f"  Excluded entries:    {result['excluded_entries']}")
        print(f"  Missing required:    {len(result['missing_required'])}")
        print(f"  Private scan find:   {result['private_scan_findings']}")
        print()

        if result["missing_required"]:
            print("❌ MISSING REQUIRED:")
            for m in result["missing_required"]:
                print(f"  - {m}")
            print()

        if result["private_scan_findings"] > 0:
            print(f"⚠️  PRIVATE SCAN ({result['private_scan_findings']} findings in generated repo):")
            for f in result["scan_findings"][:10]:
                print(f"  {f['file']}:{f['line']} {f['match']}")
            if len(result["scan_findings"]) > 10:
                print(f"  ... +{len(result['scan_findings']) - 10} more")
            print()

        if not result["missing_required"]:
            print("✅ Public repo dry-run completed.")
            print(f"   Local directory: {result['output_path']}")
            print()
            print("   Next steps (manual):")
            print(f"   1. cd {result['output_path']}")
            print("   2. uv sync")
            print("   3. uv run ordivon-verify all")
            print("   4. uv run python scripts/audit_ordivon_verify_public_wedge.py  # from private repo")
            print()
            print("   Local dry-run only. Not a real public repo.")

    return 1 if result["missing_required"] else 0


if __name__ == "__main__":
    sys.exit(main())
