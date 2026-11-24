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
# One native Cargo selection for the disposable and explicit physical lanes.
CARGO_ARGS = (
    "test",
    "--locked",
    "--lib",
    "-p",
    "ordivon-runtime-core",
    "--no-default-features",
    "--features",
    "postgres-registry-admission",
    "pg18_",
    "--",
    "--ignored",
    "--nocapture",
    "--test-threads=1",
)
# Independent Windows PG witness consumer; same disposable PG18 fixture, not
# a Windows production Writer or a second persistent test authority.
WINDOWS_PG_WITNESS_CASE = "windows_pg_bundle_consumer_reads_real_admission_without_claiming_process"
STAGE_CASE = "historical_pg_stage_is_not_an_admission_authority"


def single_case_args(case: str) -> tuple[str, ...]:
    return tuple(case if arg == "pg18_" else arg for arg in CARGO_ARGS)


WINDOWS_PG_WITNESS_ARGS = single_case_args(WINDOWS_PG_WITNESS_CASE)
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
    """Trust Cargo's exact --ignored --list test identity, not a frozen count."""
    cases = PG18_LISTED_CASE.findall(output)
    if not cases or len(cases) != len(set(cases)) or any("pg18_" not in case for case in cases):
        raise ValueError("physical PG18 native Cargo inventory missing, duplicate or out of scope")
    return frozenset(cases)


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


def observe_source_cut() -> str | None:
    """Dirty development execution is useful, but cannot attest a Git cut."""
    if __package__:
        from .verify_formal_trace import _qualified_native_source_head
    else:
        from verify_formal_trace import _qualified_native_source_head

    try:
        return _qualified_native_source_head()
    except (ValueError, OSError):
        return None


def require_same_source_cut(source_head: str | None) -> None:
    """A clean starting cut must remain qualified at observed boundaries."""
    if source_head is not None and observe_source_cut() != source_head:
        raise ValueError("PG native source cut changed or became unqualified")


def report_source_cut(source_head: str | None) -> None:
    # A local native PASS is not a claim of clean source or immutable inputs.
    if source_head is None:
        print("PG_SOURCE_CUT_UNQUALIFIED=1")
    else:
        print(f"PG_SOURCE_CUT_OBSERVED={source_head}")


def compile_pg_test_binary(cargo: str, env: dict[str, str]) -> tuple[Path, str]:
    """Build once using Cargo's original artifact identity; no test DSN at build time."""
    if __package__:
        from .verify_formal_trace import _exact_source_git_environment, _native_cargo_test_artifact, sha256
    else:
        from verify_formal_trace import _exact_source_git_environment, _native_cargo_test_artifact, sha256

    build_env = _exact_source_git_environment(env)
    build_env.pop("ORDIVON_PG_TEST_DSN", None)
    build_env.pop("ORDIVON_PG_STAGE_TEST_DSN", None)
    args = CARGO_ARGS[: CARGO_ARGS.index("--") - 1]
    built = subprocess.run(
        [cargo, *args, "--no-run", "--message-format=json"], cwd=ROOT,
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
    compiled: tuple[Path, str], args: tuple[str, ...], env: dict[str, str],
    *, identity: str | None = None, source_head: str | None = None,
) -> int:
    """List and execute one Cargo-selected libtest artifact without rebuilding."""
    if __package__:
        from .verify_formal_trace import _exact_source_git_environment, sha256
    else:
        from verify_formal_trace import _exact_source_git_environment, sha256

    binary, digest = compiled
    env = _exact_source_git_environment(env)

    def unchanged() -> None:
        require_same_source_cut(source_head)
        if binary.is_symlink() or sha256(binary) != digest:
            raise ValueError("PG native artifact changed after compilation")

    def run(*libtest_args: str) -> subprocess.CompletedProcess[str]:
        unchanged()
        result = subprocess.run(
            [str(binary), *libtest_args],
            cwd=ROOT / "crates/ordivon-runtime-core", env=env,
            capture_output=True, text=True, timeout=400,
        )
        unchanged()
        return result

    selector = args[args.index("--") - 1]
    listed = run(selector, "--ignored", "--list")
    if listed.returncode:
        raise RuntimeError(f"native libtest inventory failed (exit={listed.returncode})")
    expected = (
        listed_pg18_tests(listed.stdout) if identity is None
        else listed_single_case(listed.stdout, identity)
    )
    required = required_pg_physical_witnesses(expected) if identity is None else frozenset()
    result = run(*sorted(expected), "--exact", "--ignored", "--nocapture", "--test-threads=1")
    # libtest execution evidence comes from stdout, never compiler stderr.
    for line in result.stdout.splitlines():
        if line.startswith("test ") or line.startswith("test result:"):
            print(line[:230])
    if result.returncode:
        raise RuntimeError(f"native PostgreSQL test failed (exit={result.returncode})")
    count = exact_test_count(result.stdout, expected)
    report_source_cut(source_head)
    print(f"PG_LIBTEST_ARTIFACT_SHA256={digest}")
    if required:
        standing = "PASS" if source_head is not None else "EXECUTED_UNQUALIFIED_SOURCE"
        print(f"PG_FORMAL_CONDITIONAL_WITNESSES_{standing}={len(required)}/{len(required)}")
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
    source_head = observe_source_cut()
    count = verify_native_selection(
        compile_pg_test_binary(cargo, env),
        single_case_args(STAGE_CASE) if stage else CARGO_ARGS,
        env, identity=STAGE_CASE if stage else None, source_head=source_head,
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
            source_head = observe_source_cut()
            fixture_env = fixture_environment(os.environ, root, port)
            compiled = compile_pg_test_binary(cargo, fixture_env)
            n = verify_native_selection(compiled, CARGO_ARGS, fixture_env, source_head=source_head)
            print(f"DISPOSABLE_PG18_PASS={n}/{n}")
            n = verify_native_selection(
                compiled, WINDOWS_PG_WITNESS_ARGS, fixture_env, identity=WINDOWS_PG_WITNESS_CASE,
                source_head=source_head
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
