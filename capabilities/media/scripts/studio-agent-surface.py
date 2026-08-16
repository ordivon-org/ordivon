#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ordivon_studio.agent_surface import (
    execute_surface_action,
    surface_projection,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dependency-independent backend for Studio's thin Agent semantic surface.")
    parser.add_argument("action", nargs="?", default="surface")
    parser.add_argument("--arguments", default="{}", help="JSON object for the selected action")
    args = parser.parse_args()
    if args.action == "surface":
        value = surface_projection()
    else:
        raw = json.loads(args.arguments)
        if not isinstance(raw, dict):
            raise SystemExit("--arguments must decode to an object")
        value = execute_surface_action(args.action, raw, root=ROOT)
    json.dump(value, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
