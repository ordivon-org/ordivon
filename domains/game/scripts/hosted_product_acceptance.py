"""Consume a source-bound Actions technical preview without rebuilding it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import shutil
import subprocess
import tarfile
import tempfile
import zipfile

from rendered_product_acceptance import PRODUCT_SIZES, consume as render, digest, require
from x11_interaction_acceptance import consume as interact
from mixed_audio_acceptance import consume as audio

MAX_ARCHIVE = 256 * 1024 * 1024
MAX_EXECUTABLE = 256 * 1024 * 1024
MAX_TEXT = 64 * 1024


def names(product):
    return (f"{product}-linux-x86_64.tar.gz", f"{product}-windows-x86_64.zip",
            "BUILD_SOURCE.txt", "SHA256SUMS", "READY")


def verify_archive(path, expected_sha, source, product, target, *, platform="linux"):
    require(platform in ("linux", "windows"), "unknown native platform")
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= MAX_ARCHIVE,
            "invalid outer archive")
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha) and digest(path) == expected_sha,
            "outer archive digest differs")
    require(re.fullmatch(r"[0-9a-f]{40}", source), "invalid source commit")
    linux, windows, receipt, manifest, ready = names(product)
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        require(len(members) == 5 and {m.filename for m in members} == set(names(product)),
                "outer member inventory differs")
        for m in members:
            mode = stat.S_IFMT(m.external_attr >> 16)
            require(not m.is_dir() and mode in (0, stat.S_IFREG), "outer member not regular")
            require(0 < m.file_size <= (MAX_ARCHIVE if m.filename in (linux, windows) else MAX_TEXT),
                    "outer member too large or empty")
        require(sum(m.file_size for m in members) <= 2 * MAX_ARCHIVE, "outer expansion exceeds budget")
        require(archive.read(ready).decode() == f"COMPLETE_SOURCE_COMMIT={source}\n",
                "READY source differs")
        fields = {}
        for line in archive.read(receipt).decode().splitlines():
            k, sep, v = line.partition("=")
            require(sep and k and k not in fields, "invalid source receipt")
            fields[k] = v
        for k, v in {"SOURCE_COMMIT": source, "PRODUCT": product, "SOURCE_WORKTREE": "clean",
                     "RELEASE_PUBLISHED": "false", "QUALIFICATION": "native_headless_preview",
                     "LINUX_SCOPE": "native_headless_smoke", "WINDOWS_SCOPE": "export_only"}.items():
            require(fields.get(k) == v, f"source receipt differs: {k}")
        require(fields.get("BUILD_SCHEMA") == "1" and
                re.fullmatch(r"[0-9a-f]{40}", fields.get("SOURCE_TREE", "")) and
                all(re.fullmatch(r"[0-9a-f]{64}", fields.get(k, "")) for k in
                    ("ENGINE_SHA256", "TEMPLATE_LINUX_SHA256", "TEMPLATE_WINDOWS_SHA256")) and
                re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?\.stable\.official\.[0-9a-f]+",
                             fields.get("ENGINE", "")), "incomplete build identity")
        entries = {}
        for line in archive.read(manifest).decode().splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            require(match and match[2] not in entries, "invalid manifest")
            entries[match[2]] = match[1]
        require(set(entries) == {linux, windows, receipt}, "manifest inventory differs")
        for name in entries:
            with archive.open(name) as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            require(actual == entries[name], f"manifest digest differs: {name}")
        licenses = ({"DIALOGUE_MANAGER_LICENSE.txt", "KENNEY_ASSETS_LICENSE.txt"}
                    if product == "room-encounter" else
                    {"UPSTREAM_MIT_LICENSE.txt", "FONT_OFL_LICENSE.txt", "CREDITS.txt"})
        if platform == "windows":
            executable = materialize_windows(archive, windows, product, licenses, target)
        else:
            executable = materialize_linux(archive, linux, product, licenses, target)
        require(digest(path) == expected_sha, "outer archive changed")
        return executable, {"outer_sha256": expected_sha, "source_commit": source, "product": product,
                            "linux_archive_sha256": entries[linux], "windows_archive_sha256": entries[windows],
                            "build_source_sha256": entries[receipt], "executable_sha256": digest(executable)}



def materialize_linux(archive, name, product, licenses, target):
    with archive.open(name) as stream, tarfile.open(fileobj=stream, mode="r|gz") as tar:
        executable = target / f"{product}.x86_64"
        seen = set()
        allowed = {executable.name} | licenses
        for item in tar:
            require(item.name in allowed and item.name not in seen and item.isfile(),
                    "native member not allowed/regular")
            seen.add(item.name)
            require(0 < item.size <= (MAX_EXECUTABLE if item.name == executable.name else MAX_TEXT),
                    "native member size invalid")
            if item.name == executable.name:
                with tar.extractfile(item) as src, executable.open("xb") as out:
                    shutil.copyfileobj(src, out, length=1024 * 1024)
                require(executable.stat().st_size == item.size, "incomplete executable")
        require(seen == allowed, "native member inventory differs")
    executable.chmod(0o700)
    return executable


def materialize_windows(archive, name, product, licenses, target):
    executable = target / f"{product}.exe"
    allowed = {executable.name} | licenses
    # A seekable private copy avoids repeated decompression of the outer member.
    # Its size and digest have already been verified by the shared bundle gate.
    with tempfile.TemporaryFile() as inner:
        with archive.open(name) as src:
            shutil.copyfileobj(src, inner, length=1024 * 1024)
        inner.seek(0)
        with zipfile.ZipFile(inner) as native:
            members = native.infolist()
            require(len(members) == len(allowed) and {m.filename for m in members} == allowed,
                    "Windows native member inventory differs")
            for item in members:
                require(not item.is_dir() and stat.S_IFMT(item.external_attr >> 16) in (0, stat.S_IFREG),
                        "Windows native member not regular")
                require(0 < item.file_size <= (MAX_EXECUTABLE if item.filename == executable.name else MAX_TEXT),
                        "Windows native member size invalid")
            # Never extract paths supplied by the archive.
            with native.open(executable.name) as src, executable.open("xb") as out:
                shutil.copyfileobj(src, out, length=1024 * 1024)
            require(executable.stat().st_size == native.getinfo(executable.name).file_size,
                    "incomplete Windows executable")
    return executable


def consume(path, expected_sha, source, product):
    with tempfile.TemporaryDirectory(prefix="game-hosted-") as tmp:
        executable, identity = verify_archive(path, expected_sha, source, product, Path(tmp))
        sha = identity["executable_sha256"]
        results = {"render": render(executable, sha, product)}
        if product == "room-encounter":
            results["interaction"] = interact(executable, sha)
            results["audio"] = audio(executable, sha)
        require(all(r["status"] == "PASS" and r["executable_sha256"] == sha for r in results.values()),
                "consumer identity or disposition differs")
        return {"status": "PASS", "scope": "hosted_linux_technical_preview_consumption",
                **identity, "consumers": results,
                "windows_execution": "NOT_EVALUATED", "physical_audio": "NOT_EVALUATED",
                "human_quality": "NOT_EVALUATED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--product", choices=PRODUCT_SIZES, required=True)
    args = parser.parse_args()
    try:
        result = consume(args.archive, args.sha256, args.source, args.product)
    except (ValueError, AssertionError, OSError, zipfile.BadZipFile, tarfile.TarError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"hosted product rejected: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
