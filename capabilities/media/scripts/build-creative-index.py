#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ordivon_studio.creative_index import build_creative_index, query_creative_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or query the rebuildable Ordivon creative capability/work index.")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--creative-library-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--query")
    args = parser.parse_args()
    index = build_creative_index(ROOT, artifact_root=args.artifact_root, creative_library_root=args.creative_library_root)
    value = query_creative_index(index, args.query) if args.query else index
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
