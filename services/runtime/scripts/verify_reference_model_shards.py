#!/usr/bin/env python3
"""Bounded parallel execution of the existing 512-case Registry model property.

No generated case or assertion is discarded. Seeds are distinct and printed on
failure. The historical unsharded 512-case cargo test remains usable directly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TOTAL_CASES = 512
SEED_START = 0x0D10_2026_0000
PROPERTY = (
    "runtime::tests::registry_reference_model_properties"
    "::request_identity_and_terminal_winner_match_reference_model"
)
REPO = Path(__file__).resolve().parents[1]
PASS = re.compile(r"test result:\s*ok\.\s*1 passed;\s*0 failed;")


def plan_shards(count: int) -> list[dict[str, int]]:
    if count not in (2, 4, 8, 16):
        raise ValueError("shards must be 2, 4, 8 or 16 with exact 512-case coverage")
    return [
        {"index": i, "cases": TOTAL_CASES // count, "seed": SEED_START + i}
        for i in range(count)
    ]


def qualifies_result(returncode: int, output: str) -> bool:
    return returncode == 0 and PASS.search(output) is not None


def select_test_executable(cargo_json: str, target_dir: str) -> str:
    root = Path(target_dir).resolve()
    candidates: list[str] = []
    for line in cargo_json.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            record.get("reason") == "compiler-artifact"
            and record.get("target", {}).get("name") == "ordivon_runtime_core"
            and "lib" in record.get("target", {}).get("kind", [])
            and record.get("profile", {}).get("test") is True
            and isinstance(record.get("executable"), str)
        ):
            executable = Path(record["executable"]).resolve()
            if executable.is_relative_to(root):
                candidates.append(str(executable))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one Runtime Core test binary, found {len(candidates)}")
    return candidates[0]


def build_test_binary(timeout: int) -> str:
    # Runtime CARGO_TARGET_DIR is often /proc/self/fd/N, which is process-local.
    # Resolve it to the trusted existing build cache before child execution.
    env = dict(os.environ)
    target = env.get("CARGO_TARGET_DIR")
    if target:
        resolved = Path(target).resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("Cargo target is not a directory")
        env["CARGO_TARGET_DIR"] = str(resolved)
    else:
        resolved = REPO / "target"
    cmd = [
        env.get("CARGO_BIN") or "cargo", "test", "--locked",
        "-p", "ordivon-runtime-core", "--lib", "--no-run",
        "--message-format=json",
    ]
    result = subprocess.run(
        cmd, cwd=REPO, env=env, capture_output=True, text=True,
        check=False, timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(f"Runtime Core test build failed: {result.stderr[-2500:]}")
    binary = select_test_executable(result.stdout, str(resolved))
    if not Path(binary).is_file() or not os.access(binary, os.X_OK):
        raise RuntimeError("Runtime Core test executable does not exist or is not executable")
    listing = subprocess.run(
        [binary, PROPERTY, "--exact", "--list"],
        cwd=REPO, capture_output=True, text=True, timeout=20, check=False,
    )
    if listing.returncode or listing.stdout.count(f"{PROPERTY}: test") != 1:
        raise RuntimeError("Runtime reference-model property not found exactly once")
    return binary


def run_one(
    shard: dict[str, int], count: int, timeout: int, binary: str
) -> tuple[int, bool, str]:
    env = dict(os.environ)
    env["ORDIVON_REFERENCE_MODEL_SHARD_INDEX"] = str(shard["index"])
    env["ORDIVON_REFERENCE_MODEL_SHARD_COUNT"] = str(count)
    cmd = [binary, PROPERTY, "--exact"]
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO,
            env=env,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return shard["index"], qualifies_result(result.returncode, output), output
    except subprocess.TimeoutExpired as error:
        return shard["index"], False, f"timed out after {timeout}s: {error}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    try:
        plan = plan_shards(args.shards)
    except ValueError as e:
        parser.error(str(e))
    if not 1 <= args.parallel <= args.shards or args.timeout < 1:
        parser.error("parallel must be 1..shards, timeout positive")

    try:
        binary = build_test_binary(args.timeout)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"reference-model test binary qualification failed: {exc}", file=sys.stderr)
        return 1
    results: dict[int, bool] = {}
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(run_one, shard, args.shards, args.timeout, binary): shard
            for shard in plan
        }
        for future in as_completed(futures):
            index, success, output = future.result()
            results[index] = success
            print(
                f"reference-model shard={index}/{args.shards} "
                f"cases={plan[index]['cases']} seed={plan[index]['seed']} "
                f"status={'PASS' if success else 'FAIL'}",
                flush=True,
            )
            if not success:
                print(output[-3500:], file=sys.stderr, flush=True)
    total = sum(item["cases"] for item in plan if results.get(item["index"]))
    print(f"reference-model total qualified cases={total}/{TOTAL_CASES}", flush=True)
    return 0 if len(results) == args.shards and all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
