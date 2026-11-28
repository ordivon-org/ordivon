#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROVIDERS_DIR = Path(__file__).resolve().parents[1]
if str(PROVIDERS_DIR) not in sys.path:
    sys.path.insert(0, str(PROVIDERS_DIR))

from single_file_materialization import SingleFileProviderMaterializer, run_cli

SOURCE = Path(__file__).with_name("AuthorityValidationProvider.ps1")
ROOT = Path("/mnt/c/ProgramData/Ordivon/Workstation/Providers/AuthorityValidationProvider")
RECEIPT = Path("/mnt/c/ProgramData/Ordivon/Workstation/Providers/receipts/authority-validation-provider.json")

MATERIALIZER = SingleFileProviderMaterializer(
    source=SOURCE,
    root=ROOT,
    receipt=RECEIPT,
    materialization_kind="ordivon.workstation.authority-validation-provider-materialization",
    mismatch_error="existing authority validator bytes differ from source digest",
    materialization_fields={
        "issuesAuthority": False,
        "renewsAuthority": False,
    },
)


def main() -> int:
    return run_cli(MATERIALIZER)


if __name__ == "__main__":
    raise SystemExit(main())
