#!/usr/bin/env python3
"""Thin external-provider adapter for mCRL2 LTS equivalence checks.

The adapter does not implement equivalence itself.  It invokes a caller-supplied mCRL2
binary directory and treats provider stdout/counterexample artifacts as evidence.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def parse_ltscompare_boolean(stdout: str) -> bool:
    for line in reversed(stdout.splitlines()):
        value = line.strip().lower()
        if value == "true":
            return True
        if value == "false":
            return False
    raise ValueError("mCRL2 ltscompare output did not contain true/false verdict")


def provider_version(bin_dir: Path) -> str:
    result = _run([str(bin_dir / "mcrl22lps"), "--version"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout.splitlines()[0].strip()


def compile_spec(bin_dir: Path, spec: Path, output_prefix: Path) -> Path:
    lps = output_prefix.with_suffix(".lps")
    lts = output_prefix.with_suffix(".lts")
    first = _run([str(bin_dir / "mcrl22lps"), str(spec), str(lps)])
    if first.returncode != 0:
        raise RuntimeError(f"mcrl22lps failed: {first.stderr}")
    second = _run([str(bin_dir / "lps2lts"), str(lps), str(lts)])
    if second.returncode != 0:
        raise RuntimeError(f"lps2lts failed: {second.stderr}")
    return lts


def compare_lts(
    bin_dir: Path,
    left: Path,
    right: Path,
    *,
    equivalence: str = "bisim",
    counterexample: Path | None = None,
) -> dict[str, Any]:
    command = [str(bin_dir / "ltscompare"), "-e", equivalence]
    if counterexample is not None:
        command.extend(["-c", f"--counter-example-file={counterexample}"])
    command.extend([str(left), str(right)])
    result = _run(command)
    # ltscompare uses stdout true/false as the semantic verdict and may return 0 for
    # both equivalent and non-equivalent comparisons; do not infer semantics from rc.
    equivalent = parse_ltscompare_boolean(result.stdout)
    return {
        "equivalence": equivalence,
        "equivalent": equivalent,
        "providerReturnCode": result.returncode,
        "providerStdout": result.stdout.strip(),
        "providerStderr": result.stderr.strip(),
        "counterexampleRequested": counterexample is not None,
        "counterexamplePresent": bool(counterexample is not None and counterexample.exists()),
        "counterexamplePath": str(counterexample) if counterexample is not None else None,
    }
