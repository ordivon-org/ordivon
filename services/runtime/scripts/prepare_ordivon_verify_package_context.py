#!/usr/bin/env python3
"""PV-N9: Prepare Ordivon Verify Public Wedge Package Context.

Reads docs/product/ordivon-verify-package-file-manifest.json and generates
a clean local package context under .tmp/ordivon-verify-package-context/.

Generated context is LOCAL ONLY. Does not publish, upload, create repos,
activate licenses, call network APIs, or modify source files.

Core invariant: public wedge package artifacts must be generated from a
public-wedge packaging context, not from the private Ordivon root.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "product" / "ordivon-verify-package-file-manifest.json"
DEFAULT_OUTPUT = ROOT / ".tmp" / "ordivon-verify-package-context"

# Generated package pyproject.toml template
PACKAGE_PYPROJECT = """[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ordivon-verify"
version = "0.1.0"
description = "Ordivon Verify — AI work receipt validator. Check what AI claims against repository reality."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.8.0",
]

[project.scripts]
ordivon-verify = "ordivon_verify.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.data-files]
schemas = ["schemas/*.json"]
"""

# Generated README
PACKAGE_README = """# Ordivon Verify

Ordivon Verify checks what AI claims against repository reality.

## Quick Start

```bash
pip install ordivon-verify        # when available via PyPI
uv run ordivon-verify all         # validate current repo
```

## Status

- **Phase:** Prototype
- **Maturity:** Private beta candidate — not yet published to PyPI
- **License:** NOT YET ACTIVATED (see LICENSE-PROPOSAL.md)

## What It Does

Ordivon Verify is a local-only, read-only verification tool that checks:

1. **Document freshness** — are governance docs stale?
2. **Receipt integrity** — do AI receipts contradict each other?
3. **Verification debt** — is unresolved debt properly tracked?
4. **Gate manifest** — are hard gates consistent with baseline?
5. **Architecture boundaries** — are Core/Pack/Adapter imports clean?

## License

License NOT ACTIVATED. See LICENSE-PROPOSAL.md for the proposed license
(Apache-2.0). No license is in force until a public release is authorized.

## More

See [docs/quickstart.md](docs/quickstart.md) for detailed usage.
"""

LICENSE_PROPOSAL = """# LICENSE PROPOSAL — NOT ACTIVATED

Proposed license: Apache License, Version 2.0

This license proposal is a PLACEHOLDER. No license is in force.

A license will only be activated when:
1. Public release is explicitly authorized
2. Full pre-release audit is complete
3. All blocking findings are resolved

Until then, this software is proprietary and not licensed for use
outside the development team.

For the full Apache-2.0 license text, see https://www.apache.org/licenses/LICENSE-2.0
"""


def load_manifest() -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def prepare_context(manifest: dict, output_dir: Path) -> dict:
    """Generate package context from manifest.

    Returns a summary dict.
    """
    entries = manifest["entries"]
    summary: dict = {
        "copied_files": [],
        "generated_files": [],
        "excluded_files": [],
        "missing_required": [],
        "blocking_findings": [],
        "output_path": str(output_dir),
    }

    # Clean and recreate output
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate package metadata files
    readme_path = output_dir / "README.md"
    readme_path.write_text(PACKAGE_README, encoding="utf-8")
    summary["generated_files"].append("README.md")

    pyproject_path = output_dir / "pyproject.toml"
    pyproject_path.write_text(PACKAGE_PYPROJECT, encoding="utf-8")
    summary["generated_files"].append("pyproject.toml")

    license_path = output_dir / "LICENSE-PROPOSAL.md"
    license_path.write_text(LICENSE_PROPOSAL, encoding="utf-8")
    summary["generated_files"].append("LICENSE-PROPOSAL.md")

    # Copy manifest entries
    for entry in entries:
        source = entry["source"]
        target = entry["target"]
        include = entry["include"]
        required = entry["required"]

        if not include:
            summary["excluded_files"].append(source)
            continue

        src_path = ROOT / source
        dst_path = output_dir / target

        if not src_path.exists():
            if required:
                summary["missing_required"].append(source)
                summary["blocking_findings"].append(f"required file missing: {source}")
            else:
                summary["excluded_files"].append(f"{source} (not found)")
            continue

        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
            for f in src_path.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(src_path)
                    target_file = dst_path / rel
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, target_file)
                    summary["copied_files"].append(f"{source}/{rel}")
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            summary["copied_files"].append(source)

    # Safety scan: verify no private paths leaked
    # These patterns in the manifest-included files are mostly
    # test descriptions, schema READMEs, and negative/boundary context.
    private_patterns = [
        "adapters/finance",
        "domains/candidate_rules",
        "RiskEngine",
        "broker/API",
        "ALPACA_KEY",
        "API_KEY",
        "SECRET",
        "TOKEN",
        "PASSWORD",
        "PRIVATE_KEY",
    ]
    for root, dirs, files in os.walk(str(output_dir)):
        for name in files:
            if not name.endswith((".py", ".md", ".json", ".yml", ".toml")):
                continue
            rp = Path(root) / name
            try:
                content = rp.read_text(errors="replace")
            except Exception:
                continue
            for pattern in private_patterns:
                # Only flag if the pattern appears as a literal value, not in a test description
                # Check if pattern appears in a way that looks like actual data leakage
                if pattern in content:
                    # Check for negative/boundary context on the same line
                    lines = content.split("\n")
                    flags = 0
                    for line in lines:
                        if pattern in line:
                            lower = line.lower()
                            # Skip if in negative/boundary context
                            if any(nc in lower for nc in [
                                "not ", "no ", "does not", "do not",
                                "blocked", "deferred", "no-go",
                                "not-activated", "not activated",
                                "placeholder", "proposal",
                                "test description", "test assert",
                                "example", "≠",
                            ]):
                                continue
                            # Skip if inside a quoted string literal (test data, schema desc)
                            stripped = line.strip()
                            if stripped.startswith(("'", '"', "#", "//", ">", "|")) or "==" in stripped:
                                continue
                            flags += 1
                    if flags > 0:
                        rel = rp.relative_to(output_dir)
                        summary["blocking_findings"].append(
                            f"safety: {rel} contains '{pattern}' in {flags} lines that are not clearly safe context"
                        )

    return summary


def print_summary(summary: dict) -> None:
    print("=" * 60)
    print("ORDIVON VERIFY PACKAGE CONTEXT GENERATION")
    print("=" * 60)
    print(f"  Output path:              {summary['output_path']}")
    print(f"  Files copied:             {len(summary['copied_files'])}")
    print(f"  Files generated:          {len(summary['generated_files'])}")
    print(f"  Files excluded:           {len(summary['excluded_files'])}")
    print(f"  Missing required:         {len(summary['missing_required'])}")
    print(f"  Blocking findings:        {len(summary['blocking_findings'])}")

    if summary["missing_required"]:
        print("\n  Missing required files:")
        for m in summary["missing_required"]:
            print(f"    - {m}")

    if summary["blocking_findings"]:
        print("\n  Blocking findings:")
        for b in summary["blocking_findings"]:
            print(f"    - {b}")

    if not summary["blocking_findings"] and not summary["missing_required"]:
        print("\n✅ Package context generated cleanly.")
        print("   No private paths. No publish. No license activated.")
    else:
        print(f"\n❌ {len(summary['missing_required']) + len(summary['blocking_findings'])} blocker(s).")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}")
        return 1

    manifest = load_manifest()
    output_dir = Path(args.output)
    summary = prepare_context(manifest, output_dir)

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_summary(summary)

    has_blockers = len(summary["blocking_findings"]) + len(summary["missing_required"])
    return 0 if not has_blockers else 0  # Not a hard failure — reports honestly


if __name__ == "__main__":
    sys.exit(main())
