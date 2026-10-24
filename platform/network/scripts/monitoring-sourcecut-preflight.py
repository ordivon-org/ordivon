#!/usr/bin/env python3
"""Fail closed before a Network install could erase existing live monitoring bytes.

Two existing Owner files are compared as exact immutable source-cut values.
The check is deliberately stricter than YAML semantic equivalence: intended
changes require a separately qualified migration, never a silent overwrite.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CONFIGS = ("blackbox/blackbox.yml", "prometheus/prometheus.yml")


def verify(source: Path, live: Path) -> str:
    # The two declared configs are a closed set for this install owner.
    # Extra YAML may be a previously deployed consumer or alert rule.
    for tree in (source, live):
        for folder in ("blackbox", "prometheus"):
            directory = tree / folder
            if directory.is_symlink():
                raise ValueError(f"unmanaged monitoring directory: {folder}")
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                name = f"{folder}/{path.name}"
                if path.suffix.lower() in {".yml", ".yaml"} and name not in CONFIGS:
                    raise ValueError(f"unmanaged monitoring configuration: {name}")
    candidate = []
    for name in CONFIGS:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"invalid source monitoring file: {name}")
        candidate.append(path.read_bytes())
    present = [(live / name).exists() or (live / name).is_symlink() for name in CONFIGS]
    if not any(present):
        return "FIRST_INSTALL"
    if not all(present):
        raise ValueError("incomplete live monitoring SourceCut")
    for name, data in zip(CONFIGS, candidate, strict=True):
        path = live / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"live monitoring differs from source: {name}")
    return "IDENTICAL_SOURCECUT"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("config"))
    parser.add_argument("--live", type=Path, default=Path("/etc/network-v2"))
    args = parser.parse_args()
    try:
        standing = verify(args.source, args.live)
    except (ValueError, OSError) as exc:
        parser.exit(4, f"MONITORING_SOURCECUT=BLOCKED {exc}\n")
    print(f"MONITORING_SOURCECUT={standing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
