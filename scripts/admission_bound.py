#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path, PurePosixPath

from admission import AdmissionError, _instant, normalize


def _input_file(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise AdmissionError("bound input path must be a normal relative path")
    path = root.joinpath(*rel.parts)
    if not path.is_file() or path.is_symlink():
        raise AdmissionError(f"bound input is not one regular file: {relative}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--provider-input", required=True)
    parser.add_argument("--authority-input")
    parser.add_argument("--now")
    args = parser.parse_args()
    try:
        root_text = os.environ.get("ORDIVON_INPUT_ROOT")
        if not root_text:
            raise AdmissionError("ORDIVON_INPUT_ROOT is required; use Runtime execBound")
        root = Path(root_text)
        intent_doc = json.loads(args.intent.read_text())
        intent = intent_doc.get("intent", intent_doc)
        provider = json.loads(_input_file(root, args.provider_input).read_text())
        authority = None
        if args.authority_input:
            authority = json.loads(_input_file(root, args.authority_input).read_text())
        now = _instant(args.now) if args.now else None
        normalized = normalize({
            "schemaVersion": 2,
            "intent": intent,
            "providerObservation": provider,
            "effectAuthority": authority,
        }, now)
    except (AdmissionError, KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        print(f"BOUND_ADMISSION_DENY: {exc}", file=sys.stderr)
        return 1
    json.dump(normalized, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
