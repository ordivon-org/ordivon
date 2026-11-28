#!/usr/bin/env python3
"""Build the Windows PostgreSQL release from a locked Git source export."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
from zipfile import ZIP_DEFLATED, ZipFile

TARGET = "x86_64-pc-windows-msvc"
RUNTIME = "ordivon-runtime-pg.exe"
LAUNCHER = "ordivon-windows-pg-job-launcher.exe"
BROKER = "ordivon-windows-privileged-broker.exe"
OPERATOR_FILES = (
    "packaging/windows/materialize-ordivon-runtime-service.ps1",
    "packaging/windows/activate-ordivon-runtime-pg-service.ps1",
    "packaging/windows/windows-pg-release-provenance.ps1",
    "scripts/windows-native-runtime-r6c-acceptance.ps1",
)


def output(*args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def export_runtime_source(repo, commit, archive):
    # Git archive can apply checkout EOL conversion to text=auto members.
    # Keep the release input independent of the Windows builder EOL defaults.
    run("git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "archive",
        "--format=tar", f"--output={archive}", commit, "services/runtime", cwd=repo)


def prepare(args):
    if os.name != "nt":
        raise SystemExit("The Windows PG release requires a native Windows build host.")
    if not re.fullmatch("[a-f0-9]{40}", args.commit):
        raise SystemExit("Provide a full Git commit hash.")
    os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"
    owner = Path(__file__).resolve().parents[1]
    repo = Path(output("git", "rev-parse", "--show-toplevel", cwd=owner))
    if output("git", "rev-parse", "--verify", "HEAD^{commit}", cwd=repo) != args.commit:
        raise SystemExit("The Windows PG release requires the exact checked-out commit.")
    runtime_tree = output("git", "rev-parse", "--verify", f"{args.commit}:services/runtime", cwd=repo)
    destination = args.output.resolve()
    if destination.exists():
        raise SystemExit("Use a fresh release output directory.")

    with tempfile.TemporaryDirectory(prefix="ordivon-winpg-") as temporary:
        work = Path(temporary)
        source_tar = work / "source.tar"
        export_runtime_source(repo, args.commit, source_tar)
        run("tar.exe", "-xf", str(source_tar), cwd=work)
        source = work / "services" / "runtime"
        target_dir = args.cargo_target_directory.resolve() if args.cargo_target_directory else work / "target"
        with (source / "rust-toolchain.toml").open("rb") as stream:
            toolchain = tomllib.load(stream)["toolchain"]["channel"]
        if not args.offline:
            run("rustup", "toolchain", "install", toolchain, "--profile", "minimal", cwd=source)
        compiler = ("rustup", "run", toolchain)
        rustc = output(*compiler, "rustc", "--version", cwd=source)
        build = [
            *compiler, "cargo", "build", "--release", "--locked", "--jobs", str(args.jobs),
            "--target", TARGET, "--target-dir", str(target_dir),
            "-p", "ordivon-runtime-mcp", "--no-default-features",
            "--features", "postgres-runtime", "--bin", "ordivon-runtime-pg",
        ]
        if args.offline:
            build.append("--offline")
        run(*build, cwd=source)

        csc = Path(os.environ["SystemRoot"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        common = (str(csc), "/nologo", "/optimize+", "/platform:x64")
        launcher_source = source / "platform/windows/Ordivon.WindowsJobLauncher.cs"
        broker_source = source / "platform/windows/Ordivon.WindowsPrivilegedBroker.cs"
        run(*common, f"/out:{work / LAUNCHER}", str(launcher_source), cwd=source)
        run(*common, "/r:System.Web.Extensions.dll", "/r:System.ServiceProcess.dll",
            f"/out:{work / BROKER}", str(broker_source), cwd=source)
        files = {
            RUNTIME: target_dir / TARGET / "release" / RUNTIME,
            LAUNCHER: work / LAUNCHER,
            BROKER: work / BROKER,
            **{name: source / name for name in OPERATOR_FILES},
        }
        commitments = [
            {"path": name, "size": path.stat().st_size, "sha256": digest(path)}
            for name, path in files.items()
        ]
        manifest = {
            "schemaVersion": 1,
            "kind": "ordivon.windows-pg-release",
            "truthRole": "builder-manifest-claim-bound-to-exact-bytes-not-reproducible-build-proof",
            "source": {
                "commit": args.commit,
                "runtimeTree": runtime_tree,
                "runtimeSourceArchiveSha256": digest(source_tar),
                "cargoLockSha256": digest(source / "Cargo.lock"),
            },
            "build": {
                "target": TARGET,
                "rustc": rustc,
                "profile": "release",
                "defaultFeatures": False,
                "features": ["postgres-runtime"],
            },
            "files": commitments,
        }
        manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
        destination.mkdir(parents=True, exist_ok=False)
        archive = destination / f"ordivon-runtime-windows-pg-{args.commit}.zip"
        with ZipFile(archive, mode="x", compression=ZIP_DEFLATED) as package:
            for name, path in files.items():
                package.write(path, name)
            package.writestr("manifest.json", manifest_bytes)
        with ZipFile(archive) as package:
            if package.namelist() != [*files, "manifest.json"] or package.read("manifest.json") != manifest_bytes:
                raise SystemExit("Windows release archive file set or manifest changed.")
            for item in commitments:
                with package.open(item["path"]) as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != item["sha256"] or package.getinfo(item["path"]).file_size != item["size"]:
                    raise SystemExit(f"Windows release archive commitment mismatch: {item['path']}")
        checksum = digest(archive)
        (destination / "subjects.sha256").write_bytes(f"{checksum}  {archive.name}\n".encode("ascii"))
        print(json.dumps({"archive": str(archive), "sha256": checksum, "commit": args.commit}))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--commit", required=True)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--cargo-target-directory", type=Path)
    cli.add_argument("--jobs", type=int, default=2)
    cli.add_argument("--offline", action="store_true")
    prepare(cli.parse_args())
