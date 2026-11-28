"""Canonical single-file Workstation provider materialization.

Concrete providers own their payload-specific facts. This module owns the
shared content-addressed copy, digest verification, atomic receipt publication,
status projection, and CLI shape.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class SingleFileProviderMaterializer:
    source: Path
    root: Path
    receipt: Path
    materialization_kind: str
    mismatch_error: str
    include_source: bool = False
    materialization_fields: Mapping[str, Any] = field(default_factory=dict)
    status_kind: str | None = None

    def _target(self, source_digest: str) -> Path:
        return self.root / source_digest / self.source.name

    def materialize(self) -> dict[str, Any]:
        source_digest = sha256_file(self.source)
        target = self._target(source_digest)
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            if sha256_file(target) != source_digest:
                raise RuntimeError(self.mismatch_error)
        else:
            shutil.copyfile(self.source, target)

        payload: dict[str, Any] = {
            "schemaVersion": 1,
            "kind": self.materialization_kind,
            "sourceSha256": "sha256:" + source_digest,
            "target": str(target),
            "targetSha256": "sha256:" + sha256_file(target),
        }
        if self.include_source:
            payload["source"] = str(self.source)
        for key, value in self.materialization_fields.items():
            if key in payload:
                raise ValueError(f"materialization field overrides canonical field: {key}")
            payload[key] = value

        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.receipt.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.receipt)
        return payload

    def status(self) -> dict[str, Any]:
        source_digest = sha256_file(self.source)
        target = self._target(source_digest)
        present = target.is_file()
        payload: dict[str, Any] = {
            "schemaVersion": 1,
            "sourceSha256": "sha256:" + source_digest,
            "target": str(target),
            "present": present,
            "matches": present and sha256_file(target) == source_digest,
        }
        if self.status_kind is not None:
            payload["kind"] = self.status_kind
        return payload


def run_cli(materializer: SingleFileProviderMaterializer) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("materialize", "status"))
    args = parser.parse_args()
    payload = (
        materializer.materialize()
        if args.command == "materialize"
        else materializer.status()
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
