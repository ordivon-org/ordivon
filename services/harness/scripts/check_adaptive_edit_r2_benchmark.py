#!/usr/bin/env python3
"""Deterministic mechanical benchmark for Adaptive Edit R2.

This benchmark does not compare model intelligence. It fixes semantic source edits and
measures whether each edit codec can encode them without fuzzy matching or human byte
repair, and whether successful codecs lower to the same Runtime file edits.
"""

from __future__ import annotations

import json
from pathlib import Path

from anc_canonical import canonical_digest
from ordivon_harness.adaptive_edit import (
    AnchoredLineCodec,
    AnchoredLineEdit,
    EditCompileError,
    ExactReplacementCodec,
    ExactReplacementEdit,
    SourceSnapshot,
    anchored_line_plan,
    exact_replacement_plan,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/harness-replacement-repository-repair-v1/allocation.py"
ORACLE = ROOT / "evals/harness-repository-repair-001/oracle/allocation.py"


def digest_text(text: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def apply_file_patch(content: str, file_patch) -> str:
    """Apply CanonicalFilePatch to memory using Runtime-compatible positions."""

    def offset(line: int, column: int) -> int:
        lines = content.split("\n")
        if line < 1 or line > len(lines):
            raise ValueError("line outside content")
        if column < 0 or column > len(lines[line - 1]):
            raise ValueError("column outside content")
        before = sum(len(item) + 1 for item in lines[: line - 1])
        return before + len(lines[line - 1][:column])

    resolved = []
    for edit in file_patch.edits:
        start = offset(edit.start_line, edit.start_column)
        end = offset(edit.end_line, edit.end_column)
        if content[start:end] != edit.expected_text:
            raise ValueError("compiled expectedText differs from benchmark source")
        resolved.append((start, end, edit.replacement))
    result = content
    for start, end, replacement in sorted(resolved, reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def repository_repair_case() -> dict:
    source = FIXTURE.read_text(encoding="utf-8")
    target = ORACLE.read_text(encoding="utf-8")
    snapshot = SourceSnapshot("allocation.py", digest_text(source), source)
    old = "    return [(total * weight) // weight_total for weight in weights]"
    new = target[target.index("    allocations =") :].rstrip("\n")

    exact = exact_replacement_plan(
        (snapshot,),
        (ExactReplacementEdit("allocation.py", old, new),),
    )
    line = source.split("\n").index(old) + 1
    anchor = snapshot.line_anchor(line)
    anchored = anchored_line_plan(
        (snapshot,),
        (AnchoredLineEdit("allocation.py", anchor, anchor, new),),
    )
    exact_after = apply_file_patch(source, exact.files[0])
    anchored_after = apply_file_patch(source, anchored.files[0])
    return {
        "case": "HARNESS-REPO-REPAIR-001",
        "sourceDigest": snapshot.digest,
        "targetDigest": digest_text(target),
        "exactReplacement": {
            "compiled": True,
            "matchesTarget": exact_after == target,
            "runtimeFilesDigest": canonical_digest(exact.runtime_files()),
        },
        "anchoredLine": {
            "compiled": True,
            "matchesTarget": anchored_after == target,
            "runtimeFilesDigest": canonical_digest(anchored.runtime_files()),
        },
        "sameRuntimePatch": exact.runtime_files() == anchored.runtime_files(),
        "humanByteRepair": False,
        "fuzzyMatching": False,
    }


def duplicate_text_case() -> dict:
    source = "value = 1\nkeep = True\nvalue = 1\n"
    target = "value = 1\nkeep = True\nvalue = 2\n"
    snapshot = SourceSnapshot("duplicate.py", digest_text(source), source)
    exact_error = None
    try:
        exact_replacement_plan(
            (snapshot,),
            (ExactReplacementEdit("duplicate.py", "value = 1", "value = 2"),),
        )
    except EditCompileError as error:
        exact_error = str(error)

    anchor = snapshot.line_anchor(3)
    anchored = anchored_line_plan(
        (snapshot,),
        (AnchoredLineEdit("duplicate.py", anchor, anchor, "value = 2"),),
    )
    anchored_after = apply_file_patch(source, anchored.files[0])
    return {
        "case": "duplicate-text-addressing",
        "sourceDigest": snapshot.digest,
        "targetDigest": digest_text(target),
        "exactReplacement": {
            "compiled": exact_error is None,
            "failure": exact_error,
            "expectedFailure": "ambiguous" in (exact_error or ""),
        },
        "anchoredLine": {
            "compiled": True,
            "matchesTarget": anchored_after == target,
        },
        "interpretation": (
            "Exact replacement correctly refuses an ambiguous semantic target; "
            "anchored addressing distinguishes the intended repeated line without fuzzy matching."
        ),
    }


def stale_anchor_case() -> dict:
    source = "one\ntwo\nthree\n"
    before = SourceSnapshot("stale.txt", digest_text(source), source)
    anchor = before.line_anchor(2)
    changed_source = "one\nTWO\nthree\n"
    changed = SourceSnapshot("stale.txt", digest_text(changed_source), changed_source)
    failure = None
    try:
        anchored_line_plan(
            (changed,),
            (AnchoredLineEdit("stale.txt", anchor, anchor, "replacement"),),
        )
    except EditCompileError as error:
        failure = str(error)
    return {
        "case": "stale-anchor",
        "beforeDigest": before.digest,
        "changedDigest": changed.digest,
        "anchoredLine": {
            "compiled": failure is None,
            "failure": failure,
            "expectedFailure": "does not match" in (failure or ""),
        },
    }


def build_report() -> dict:
    cases = [repository_repair_case(), duplicate_text_case(), stale_anchor_case()]
    checks = {
        "repositoryRepairExactMatchesOracle": cases[0]["exactReplacement"]["matchesTarget"],
        "repositoryRepairAnchoredMatchesOracle": cases[0]["anchoredLine"]["matchesTarget"],
        "repositoryRepairSameRuntimePatch": cases[0]["sameRuntimePatch"],
        "ambiguousExactFailsClosed": cases[1]["exactReplacement"]["expectedFailure"],
        "anchoredDisambiguatesRepeatedLine": cases[1]["anchoredLine"]["matchesTarget"],
        "staleAnchorFailsClosed": cases[2]["anchoredLine"]["expectedFailure"],
    }
    report = {
        "schemaVersion": 1,
        "kind": "ordivon.adaptive-edit-r2-mechanical-benchmark",
        "scope": (
            "Deterministic mechanical ACI benchmark only; no Provider/model quality, latency, "
            "token efficiency, or broad repository-repair success claim."
        ),
        "codecs": [ExactReplacementCodec.codec_id, AnchoredLineCodec.codec_id],
        "cases": cases,
        "checks": checks,
        "allChecksPassed": all(checks.values()),
        "historicalContext": {
            "evidence": "evidence/harness-rsi-p2-self-modification-5360130.json",
            "observation": (
                "Historical P2 recorded two Agent-authored malformed unified diffs rejected "
                "before materialization, followed by successful exact-oldText/newText encoding."
            ),
            "notReplayedAsBenchmarkData": True,
        },
    }
    report["reportDigest"] = canonical_digest(report)
    return report


def main() -> int:
    report = build_report()
    if not report["allChecksPassed"]:
        raise SystemExit(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
