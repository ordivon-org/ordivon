#!/usr/bin/env python3
"""Native PG verification with one test-set acceptance check for all three lanes.

Default: disposable /var/tmp cluster, no operator DSN or TCP listener.
Explicit physical/stage lanes require their respective operator test DSN;
they never start a cluster and never fall back to another lane's DSN.
"""

from __future__ import annotations

import os
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# One native Cargo build profile for every PG lane. Selection uses native inventory.
CARGO_ARGS = (
    "test",
    "--locked",
    "--lib",
    "-p",
    "ordivon-runtime-core",
    "--no-default-features",
    "--features",
    "postgres-registry-admission",
)
# Independent Windows PG witness consumer; same disposable PG18 fixture, not
# a Windows production Writer or a second persistent test authority.
WINDOWS_PG_WITNESS_CASE = "windows_pg_bundle_consumer_reads_real_admission_without_claiming_process"
STAGE_CASE = "historical_pg_stage_is_not_an_admission_authority"

# Distinct native capability lanes, not an allowlist of PG test names.
# Every other ignored test in the compiled PG-only Core is part of the
# disposable PG portfolio, even when its module or business name changes.
SYSTEMD_ONLY_CASE = "native_systemctl_missing_unit_is_explicit_negative_evidence"
SEPARATE_LANES = frozenset({STAGE_CASE, WINDOWS_PG_WITNESS_CASE, SYSTEMD_ONLY_CASE})

PG18_LISTED_CASE = re.compile(r"^(\S+): test$", re.M)
PG18_EXECUTED_CASE = re.compile(r"^test (\S+) \.\.\. ok$", re.M)
PG18_RESULT = re.compile(r"^test result: ok\. (\d+) passed; 0 failed; 0 ignored;", re.M)


def fixture_environment(original: dict[str, str], socket_dir: Path, port: int) -> dict[str, str]:
    """Override even an inherited production DSN; never propagate stage authority."""
    result = dict(original)
    result["ORDIVON_PG_TEST_DSN"] = f"host={socket_dir} port={port} user=postgres dbname=postgres"
    result.pop("ORDIVON_PG_STAGE_TEST_DSN", None)
    return cargo_environment(result)


def cargo_environment(original: dict[str, str]) -> dict[str, str]:
    result = dict(original)
    # Runtime passes an FD-backed Cargo cache to the native tool invocation.
    # Python's subprocess closes unrelated FDs; resolve only this compiler
    # cache to the *same* actual directory before spawning a child Cargo.
    cargo_dir = result.get("CARGO_TARGET_DIR", "")
    if cargo_dir.startswith("/proc/self/fd/"):
        actual = Path(cargo_dir).resolve(strict=True)
        if not actual.is_dir():
            raise RuntimeError("FD-backed Cargo target is not an existing directory")
        result["CARGO_TARGET_DIR"] = str(actual)
    return result


def listed_pg18_tests(output: str) -> frozenset[str]:
    """Partition the compiled ignored inventory, not a test-name prefix.

    PG-only Core has explicit historical-stage, Windows database witness,
    and systemd-only lanes. New ordinary ignored tests cannot silently
    escape by changing their names. Duplicate separate lanes fail closed.
    """
    cases = PG18_LISTED_CASE.findall(output)
    if not cases or len(cases) != len(set(cases)):
        raise ValueError("physical PG18 native inventory missing or duplicate")
    excluded = [case for case in cases if case.rsplit("::", 1)[-1] in SEPARATE_LANES]
    if len(excluded) != len({case.rsplit("::", 1)[-1] for case in excluded}):
        raise ValueError("physical PG18 separate lane identity is ambiguous")
    expected = frozenset(cases) - set(excluded)
    if not expected:
        raise ValueError("physical PG18 native inventory contains no PG portfolio tests")
    return expected


def exact_test_count(output: str, expected: frozenset[str]) -> int:
    """Require every natively listed test actually pass once, including new modules."""
    observed = PG18_EXECUTED_CASE.findall(output)
    summaries = [int(n) for n in PG18_RESULT.findall(output)]
    if (
        not expected
        or len(observed) != len(expected)
        or len(observed) != len(set(observed))
        or set(observed) != expected
        or summaries != [len(expected)]
    ):
        raise ValueError(
            f"physical PG18 result unqualified: expected={len(expected)} observed={len(observed)} summaries={summaries}"
        )
    return len(observed)


def listed_single_case(output: str, identity: str) -> frozenset[str]:
    cases = PG18_LISTED_CASE.findall(output)
    if len(cases) != 1 or cases[0].rsplit("::", 1)[-1] != identity:
        raise ValueError("physical native Cargo inventory must contain exactly the named witness")
    return frozenset(cases)


def required_pg_physical_witnesses(inventory: frozenset[str]) -> frozenset[str]:
    """Bind the physical lane to the same named formal conditional obligations.

    The general inventory remains dynamic; removing one required witness
    must not look green merely because the remaining selected tests pass.
    """
    if __package__:
        from .verify_formal_trace import TRACE, native_profile_trace, validate_pg_witnesses, _native_witness_name
    else:
        from verify_formal_trace import TRACE, native_profile_trace, validate_pg_witnesses, _native_witness_name

    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    errors = validate_pg_witnesses(trace)
    if errors:
        raise ValueError("PG formal physical obligations unqualified: " + "; ".join(errors))
    return frozenset(
        _native_witness_name(row, set(inventory))
        for row in native_profile_trace(trace, "pg")["conditionalAcceptanceTests"]
    )


def compile_pg_test_binary(cargo: str, env: dict[str, str]) -> tuple[Path, str]:
    """Build once using Cargo's original artifact identity; no test DSN at build time."""
    if __package__:
        from .verify_formal_trace import _native_cargo_test_artifact, sha256
    else:
        from verify_formal_trace import _native_cargo_test_artifact, sha256

    build_env = dict(env)
    build_env.pop("ORDIVON_PG_TEST_DSN", None)
    build_env.pop("ORDIVON_PG_STAGE_TEST_DSN", None)
    built = subprocess.run(
        [cargo, *CARGO_ARGS, "--no-run", "--message-format=json"], cwd=ROOT,
        env=build_env, capture_output=True, text=True, timeout=400,
    )
    if built.returncode:
        raise RuntimeError(f"native Cargo compilation failed (exit={built.returncode})")
    artifact = _native_cargo_test_artifact(built.stdout, "pg")
    expected_source = ROOT / "crates/ordivon-runtime-core/src/lib.rs"
    if Path(artifact["target"]["src_path"]).resolve() != expected_source.resolve():
        raise ValueError("Cargo emitted an unexpected PG artifact source module")
    binary = Path(artifact["executable"])
    target = Path(env.get("CARGO_TARGET_DIR", str(ROOT / "target")))
    if not target.is_absolute():
        target = ROOT / target
    if (
        not binary.is_absolute() or not binary.is_file() or binary.is_symlink()
        or not binary.resolve().is_relative_to(target.resolve())
    ):
        raise ValueError("Cargo emitted PG artifact outside qualified build target")
    return binary, sha256(binary)


def verify_native_selection(
    compiled: tuple[Path, str], env: dict[str, str],
    *, identity: str | None = None,
) -> int:
    """List and execute one Cargo-selected libtest artifact without rebuilding."""
    if __package__:
        from .verify_formal_trace import sha256
    else:
        from verify_formal_trace import sha256

    binary, digest = compiled
    # Keep upstream libtest capture enabled: test-body diagnostics are
    # not execution receipts. Ignore inherited opt-out as well as explicit flags.
    test_env = dict(env)
    test_env.pop("RUST_TEST_NOCAPTURE", None)

    def unchanged() -> None:
        if binary.is_symlink() or sha256(binary) != digest:
            raise ValueError("PG native artifact changed after compilation")

    def run(*libtest_args: str) -> subprocess.CompletedProcess[str]:
        unchanged()
        result = subprocess.run(
            [str(binary), *libtest_args],
            cwd=ROOT / "crates/ordivon-runtime-core", env=test_env,
            capture_output=True, text=True, timeout=400,
        )
        unchanged()
        return result

    # Discover all ignored cases of this exact binary before partitioning.
    # The explicit historical-stage/Windows witness remains a single lane.
    listed = run(*([identity] if identity is not None else []), "--ignored", "--list")
    if listed.returncode:
        raise RuntimeError(f"native libtest inventory failed (exit={listed.returncode})")
    expected = (
        listed_pg18_tests(listed.stdout) if identity is None
        else listed_single_case(listed.stdout, identity)
    )
    required = required_pg_physical_witnesses(expected) if identity is None else frozenset()
    result = run(*sorted(expected), "--exact", "--ignored", "--test-threads=1")
    # libtest execution evidence comes from stdout, never compiler stderr.
    for line in result.stdout.splitlines():
        if line.startswith("test ") or line.startswith("test result:"):
            print(line[:230])
    if result.returncode:
        raise RuntimeError(f"native PostgreSQL test failed (exit={result.returncode})")
    count = exact_test_count(result.stdout, expected)
    print(f"PG_LIBTEST_ARTIFACT_SHA256={digest}")
    if required:
        print(f"PG_FORMAL_CONDITIONAL_WITNESSES_PASS={len(required)}/{len(required)}")
    return count


def explicit_lane(lane: str) -> int:
    stage = lane == "--stage"
    variable = "ORDIVON_PG_STAGE_TEST_DSN" if stage else "ORDIVON_PG_TEST_DSN"
    if not os.environ.get(variable, "").strip():
        print(f"{variable} is required for PostgreSQL qualification", file=sys.stderr)
        return 2
    cargo = shutil.which("cargo")
    if cargo is None:
        raise RuntimeError("cargo must be installed")
    env = cargo_environment(os.environ)
    env.pop("ORDIVON_PG_TEST_DSN" if stage else "ORDIVON_PG_STAGE_TEST_DSN", None)
    count = verify_native_selection(
        compile_pg_test_binary(cargo, env),
        env, identity=STAGE_CASE if stage else None,
    )
    print(f"{'STAGE' if stage else 'PHYSICAL'}_PG18_PASS={count}/{count}")
    return 0


def run_checked(command: list[str], *, timeout: int = 90) -> None:
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if process.returncode != 0:
        raise RuntimeError(
            f"disposable PostgreSQL fixture command failed ({command[0]},"
            f" exit={process.returncode}): {process.stderr[-1500:]}"
        )


def main() -> int:
    if sys.platform != "linux":
        raise RuntimeError("disposable PG18 fixture supports Linux only")
    initdb = shutil.which("initdb")
    pg_ctl = shutil.which("pg_ctl")
    cargo = shutil.which("cargo")
    if not all((initdb, pg_ctl, cargo)):
        raise RuntimeError("initdb, pg_ctl and cargo must be installed")
    prefix: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ordivon-pg18-", dir="/var/tmp") as raw:
        root = Path(raw)
        if os.geteuid() == 0:
            import pwd

            account = pwd.getpwnam("nobody")
            os.chown(root, account.pw_uid, account.pw_gid)
            runuser = shutil.which("runuser")
            if not runuser:
                raise RuntimeError("root cannot start PostgreSQL without runuser")
            prefix = [runuser, "-u", "nobody", "--"]
        data_dir = root / "data"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        started = False
        try:
            run_checked(
                prefix
                + [
                    initdb,
                    "-D",
                    str(data_dir),
                    "-A",
                    "trust",
                    "-U",
                    "postgres",
                    "--no-locale",
                    "--encoding=UTF8",
                ],
                timeout=90,
            )
            run_checked(
                prefix
                + [
                    pg_ctl,
                    "-D",
                    str(data_dir),
                    "-o",
                    f"-k {root} -h '' -p {port} -c fsync=off",
                    "-l",
                    str(root / "postgres.log"),
                    "-w",
                    "start",
                ],
                timeout=60,
            )
            started = True
            source = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
            dirty = bool(subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip())
            print(f"sourceCut={source} standing={'DIRTY_UNQUALIFIED' if dirty else 'CLEAN'}")
            fixture_env = fixture_environment(os.environ, root, port)
            compiled = compile_pg_test_binary(cargo, fixture_env)
            n = verify_native_selection(compiled, fixture_env)
            print(f"DISPOSABLE_PG18_PASS={n}/{n}")
            n = verify_native_selection(
                compiled, fixture_env, identity=WINDOWS_PG_WITNESS_CASE
            )
            print(f"DISPOSABLE_WINDOWS_PG_WITNESS_PASS={n}/{n}")
        finally:
            if started:
                run_checked(
                    prefix + [pg_ctl, "-D", str(data_dir), "-m", "immediate", "-w", "stop"],
                    timeout=45,
                )
    print("DISPOSABLE_POSTGRESQL_STOPPED_AND_REMOVED=1")
    return 0


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        if not args:
            raise SystemExit(main())
        if args in (["--physical"], ["--stage"]):
            raise SystemExit(explicit_lane(args[0]))
        print("usage: pg_disposable_physical.py [--physical | --stage]", file=sys.stderr)
        raise SystemExit(2)
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"PG18_VERIFICATION_UNQUALIFIED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
