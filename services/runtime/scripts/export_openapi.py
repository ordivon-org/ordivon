from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.main import app

SNAPSHOT_PATH = ROOT_DIR / "tests" / "contracts" / "openapi.snapshot.json"


def main() -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = app.openapi()
    SNAPSHOT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(SNAPSHOT_PATH)


if __name__ == "__main__":
    main()
