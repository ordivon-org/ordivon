#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROVIDERS_DIR = Path(__file__).resolve().parents[1]
if str(PROVIDERS_DIR) not in sys.path:
    sys.path.insert(0, str(PROVIDERS_DIR))

from single_file_materialization import SingleFileProviderMaterializer, run_cli

SOURCE = Path(__file__).with_name("WindowsWslServiceControlProvider.ps1")
ROOT = Path("/mnt/c/ProgramData/Ordivon/Workstation/Providers/WindowsWslServiceControlProvider")
RECEIPT = Path(
    "/mnt/c/ProgramData/Ordivon/Workstation/Providers/receipts/windows-wsl-service-control-provider.json"
)

MATERIALIZER = SingleFileProviderMaterializer(
    source=SOURCE,
    root=ROOT,
    receipt=RECEIPT,
    materialization_kind="ordivon.workstation.windows-wsl-service-control-provider-materialization",
    mismatch_error="materialized provider digest mismatch",
    materialization_fields={"targetNodeIds": ["linux-local"]},
)


def main() -> int:
    return run_cli(MATERIALIZER)


if __name__ == "__main__":
    raise SystemExit(main())
