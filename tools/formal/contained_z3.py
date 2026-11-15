"""One explicitly bounded Z3 media-model check using existing Formal inputs.

This is a **new isolated single-consumer run**, never reuse of an older
Formal mathematical proof, full system proof, or installed currentness.
Linux-only: native Bubblewrap restricts Z3's visible filesystem to a
staged executable, a finite loader-observed library set and empty /tmp.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / "tools" / "formal"
MODEL = "capabilities/media/formal/LoudnessProfileSafety.smt2"
EXPECTED = ("sat", "unsat", "sat")
SHARED_LIB_ROOT = Path("/usr/lib")


def _native_formal():
    source = FORMAL / "verify.py"
    spec = importlib.util.spec_from_file_location("ordivon_existing_formal", source)
    if spec is None or spec.loader is None:
        raise ValueError("existing Formal producer cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(*args: str) -> bytes:
    safe_env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    safe_env["GIT_GRAFT_FILE"] = os.devnull
    return subprocess.check_output(
        ["/usr/bin/git", "--no-replace-objects", "-C", str(ROOT), *args],
        env=safe_env,
        stderr=subprocess.PIPE,
    )


def _stage_verified_file(source: Path, destination: Path, expected_digest: str) -> None:
    if (
        source.is_symlink()
        or not source.is_file()
        or not stat.S_ISREG(source.stat().st_mode)
    ):
        raise ValueError("selected Formal input must be a regular file")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise ValueError("unqualified Formal input digest")
    shutil.copyfile(source, destination)
    destination.chmod(0o444)
    with destination.open("rb") as stream:
        observed = hashlib.file_digest(stream, "sha256").hexdigest()
    if observed != expected_digest:
        raise ValueError("selected tool input changed before isolated execution")


def _command_for_staged_inputs(
    *,
    z3_source: Path,
    z3_digest: str,
    libraries: dict[str, str],
    stage: Path,
) -> tuple[list[str], list[dict[str, str]]]:
    """No whole-root, /etc, /home, /proc, /dev, or network mount."""
    if (
        Path("/lib").readlink() != Path("usr/lib")
        or Path("/lib64").readlink() != Path("usr/lib")
        or shutil.which("bwrap") != "/usr/bin/bwrap"
        or not libraries
    ):
        raise ValueError("unsupported local Bubblewrap/ELF namespace layout")
    ordered = sorted(libraries.items())
    command = [
        "/usr/bin/bwrap",
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--clearenv",
        "--tmpfs",
        "/",
        "--dir",
        "/usr",
        "--dir",
        "/usr/lib",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib",
        "/lib64",
        "--tmpfs",
        "/tmp",
    ]
    staged: list[dict[str, str]] = []
    binary = stage / "z3"
    # The native producer resolves its selected mise executable.
    _stage_verified_file(z3_source, binary, z3_digest)
    # Staged executable is read+execute, never writable.
    binary.chmod(0o555)
    command.extend(("--ro-bind", str(binary), "/z3"))
    staged.append({"guestPath": "/z3", "sha256": z3_digest})
    soname_aliases: set[str] = set()
    for index, (path, digest) in enumerate(ordered):
        original = Path(path)
        if original.parent != SHARED_LIB_ROOT or original.is_symlink():
            raise ValueError("isolated Z3 only supports finite /usr/lib regular inputs")
        selected = stage / f"lib-{index}"
        _stage_verified_file(original, selected, digest)
        # The ELF PT_INTERP loader is an actual executable. Its staged
        # content is immutable/read-only but still requires executable mode.
        if original.name == "ld-linux-x86-64.so.2":
            selected.chmod(0o555)
        command.extend(("--ro-bind", str(selected), path))
        staged.append({"guestPath": path, "sha256": digest})
        # This system resolves libstdc++.so.6 to an immutable concrete .so.6.N
        # while the ELF loader requests the public SONAME. No broad /usr mount.
        match = re.fullmatch(r"(libstdc\+\+\.so\.6)\.\d+(?:\.\d+)*", original.name)
        if match:
            alias = "/usr/lib/" + match.group(1)
            soname_aliases.add(alias)
            command.extend(("--symlink", original.name, alias))
    if len(soname_aliases) > 1:
        raise ValueError("ambiguous C++ runtime SONAME")
    command.extend(("--chdir", "/tmp", "--", "/z3", "-smt2", "-in"))
    return command, staged


def run_bounded_media_z3() -> dict[str, object]:
    """Run only one existing real media SMT model under restricted mounts."""
    native = _native_formal()
    native.require_unmodified_elf_loader_environment()
    source = native.qualified_source_cut()
    sha = source["gitHead"]
    model_file = ROOT / MODEL
    original_model = _git("show", f"{sha}:{MODEL}")
    if (
        model_file.is_symlink()
        or not model_file.is_file()
        or model_file.read_bytes() != original_model
    ):
        raise ValueError("media SMT input is not the exact Git SourceCut content")
    if MODEL not in source["sourceBlobs"]:
        raise ValueError("media SMT source is absent from existing Formal producer")
    # The runner also belongs to this immutable Git SourceCut. Native Formal
    # SOURCE_FILES describes the OLD producer readset; never add this optional
    # runner to it simply to make the original proof appear current.
    runner = "tools/formal/contained_z3.py"
    if Path(__file__).is_symlink() or Path(__file__).read_bytes() != _git(
        "show", f"{sha}:{runner}"
    ):
        raise ValueError("contained Z3 runner is not exact Git SourceCut content")
    z3 = native.qualified_tool_binaries()["z3"]
    binary = Path(z3["path"])
    loader = native.observed_z3_elf_dependencies(binary)
    if loader["entrypointSha256"] != z3["sha256"]:
        raise ValueError("native Z3 executable and loader input disagree")
    libs = loader["resolvedLibraries"]
    if not isinstance(libs, dict) or len(libs) > 32:
        raise ValueError("native Z3 input set is absent or excessive")
    # The shared /tmp is tmpfs and cannot be used as an executable
    # Bubblewrap bind source on this Runtime. Pin staged bytes on the
    # workspace ext4 instead; cleanup remains automatic.
    with tempfile.TemporaryDirectory(prefix=".ordivon-contained-z3-", dir=ROOT) as tmp:
        stage = Path(tmp)
        stage.chmod(0o755)
        command, staged = _command_for_staged_inputs(
            z3_source=binary,
            z3_digest=z3["sha256"],
            libraries=libs,
            stage=stage,
        )
        result = subprocess.run(
            command,
            input=original_model.decode("utf-8"),
            text=True,
            capture_output=True,
            timeout=35,
            check=False,
        )
        if (
            result.returncode != 0
            or tuple(result.stdout.strip().splitlines()) != EXPECTED
        ):
            raise ValueError(
                "contained Z3 consumer failed expected SAT/UNSAT/SAT check: "
                + result.stderr[-450:]
            )
        # Boundary falsifier: this valid host file must not be accessible
        # through the guest, whose root contains no /etc mount.
        if not Path("/etc/passwd").is_file():
            raise ValueError("host negative-control fixture unavailable")
        negative = subprocess.run(
            [*command[:-3], "/z3", "/etc/passwd"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if (
            negative.returncode == 0
            or "failed to open file" not in (negative.stderr + negative.stdout).lower()
        ):
            raise ValueError("guest host-file denial negative control inconclusive")
        # Confirm staged bytes did not change after both subprocesses.
        for item in staged:
            guest = item["guestPath"]
            path = stage / (
                "z3" if guest == "/z3" else f"lib-{sorted(libs).index(guest)}"
            )
            with path.open("rb") as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != item["sha256"]:
                    raise ValueError(
                        "staged selected input changed after isolated execution"
                    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.contained-z3-selected-input-consumer",
        "sourceCut": sha,
        "model": MODEL,
        "modelSha256": hashlib.sha256(original_model).hexdigest(),
        "runnerSourceBlob": _git("rev-parse", f"{sha}:tools/formal/contained_z3.py")
        .decode()
        .strip(),
        "outcomes": list(EXPECTED),
        "hostEtcPasswdAccessDenied": True,
        "visibleReadOnlyInputs": staged,
        "filesystemBoundary": "bubblewrap-empty-root-selected-ELF-inputs-only",
        "networkNamespaceIsolated": True,
        "guestProcDevEtcNotMounted": True,
        "claimScope": "THIS_Z3_MEDIA_SAT_UNSAT_SAT_CONSUMER_ONLY",
        "historicalProofReuseAdmissible": False,
        "modelToImplementationRefinement": "UNKNOWN",
        "installedCurrentness": "UNKNOWN",
    }


def main() -> None:
    print(json.dumps(run_bounded_media_z3(), sort_keys=True))


if __name__ == "__main__":
    main()
