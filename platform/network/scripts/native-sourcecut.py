#!/usr/bin/env python3
"""Pure Network SourceCut classifier; no installation, service or network effects.

Reuse Python stdlib, OS file identity and native systemctl.  This CLI only
projects MATCH, DRIFT or UNKNOWN; Go Task owns task ordering and systemd owns
runtime lifecycle.  A failed observation is NEVER installation permission.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys


class Unknown(RuntimeError):
    """An observation was inconclusive, not proof of source drift."""


def accessible_parent(path: Path) -> None:
    """Allow a missing install directory while refusing symlinked parents."""
    probe = path.parent
    for _ in range(256):
        try:
            info = probe.lstat()
        except FileNotFoundError:
            pass  # First installation may legitimately create an owner tree.
        except OSError as exc:
            raise Unknown(f"installation ancestor unreadable: {exc}") from exc
        else:
            if not stat.S_ISDIR(info.st_mode):
                raise Unknown(f"installation ancestor is not a genuine directory: {probe}")
            if not os.access(probe, os.X_OK):
                raise Unknown(f"installation ancestor is inaccessible: {probe}")
        # Check *every* ancestor: an earlier symlink must not evade admission
        # merely because the immediate parent was a real directory.
        if probe.parent == probe:
            return
        probe = probe.parent
    raise Unknown("installation parent path has excessive depth")


def file_digest(path: Path, *, destination: bool) -> tuple[str, int] | None:
    # Even an existing regular file could be reached through a symlink in
    # an intermediate directory. Its absolute identity is not authorized.
    accessible_parent(path)
    try:
        before = path.lstat()
    except FileNotFoundError as exc:
        if destination:
            accessible_parent(path)
            return None
        raise Unknown(f"source does not exist: {path}") from exc
    except OSError as exc:
        raise Unknown(f"file observation failed: {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise Unknown(f"not a regular owned file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        with os.fdopen(os.open(path, flags), "rb") as stream:
            held = os.fstat(stream.fileno())
            if not stat.S_ISREG(held.st_mode):
                raise Unknown(f"non-regular file opened: {path}")
            if (held.st_dev, held.st_ino) != (before.st_dev, before.st_ino):
                raise Unknown(f"file changed identity during admission: {path}")
            digest = hashlib.sha256()
            while data := stream.read(65536):
                digest.update(data)
            after = os.fstat(stream.fileno())
        current = path.lstat()
    except Unknown:
        raise
    except OSError as exc:
        raise Unknown(f"file read failed: {path}: {exc}") from exc
    baseline = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    for check in (held, after, current):
        got = (check.st_dev, check.st_ino, check.st_size, check.st_mtime_ns, check.st_ctime_ns)
        if got != baseline:
            raise Unknown(f"file mutated during admission: {path}")
    return digest.hexdigest(), stat.S_IMODE(current.st_mode)


def absent_state(path: Path) -> bool:
    accessible_parent(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise Unknown(f"cannot inspect retired path: {path}: {exc}") from exc
    if stat.S_ISREG(info.st_mode):
        return True
    raise Unknown(f"retired path has unknown owner/type: {path}")


def systemd(*args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(["systemctl", *args], capture_output=True,
                              text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unknown(f"systemd query unavailable: {exc}") from exc
    output = proc.stdout.strip()
    if "\n" in output:
        raise Unknown("unexpected multiline systemd observation")
    return proc.returncode, output


def classify(args: argparse.Namespace) -> str:
    drift = False
    missing_units: set[str] = set()
    mappings = list(args.file)
    installed_modes: dict[str, int] = {}
    for installed, octal in args.mode:
        if not Path(installed).is_absolute() or installed in installed_modes:
            raise Unknown(f"invalid or repeated installed mode path: {installed}")
        try:
            expected = int(octal, 8)
        except ValueError as exc:
            raise Unknown(f"invalid installed mode for {installed}") from exc
        if not 0 <= expected <= 0o7777:
            raise Unknown(f"out-of-range installed mode for {installed}")
        installed_modes[installed] = expected
    for pattern, target_dir in args.glob:
        if not target_dir.endswith("/"):
            raise Unknown("glob target must be a directory ending in /")
        if Path(pattern).is_symlink():
            raise Unknown(f"glob path is not owned: {pattern}")
        paths = sorted(glob.glob(pattern))
        if not paths:
            raise Unknown(f"source glob has no matches: {pattern}")
        for candidate in paths:
            mappings.append((candidate, target_dir + Path(candidate).name))
    if not any((args.file, args.glob, args.absent, args.unit_enabled, args.unit_loaded)):
        raise Unknown("empty SourceCut admission is not evidence")
    targets = {dest for _, dest in mappings}
    if installed_modes.keys() - targets:
        raise Unknown("installed mode declaration without matching file SourceCut")
    for source, installed in mappings:
        if not Path(installed).is_absolute():
            raise Unknown(f"installed path must be absolute: {installed}")
        source_identity = file_digest(Path(source), destination=False)
        installed_identity = file_digest(Path(installed), destination=True)
        if installed_identity is None:
            drift = True
            if installed.startswith("/etc/systemd/system/"):
                missing_units.add(Path(installed).name)
        elif source_identity[0] != installed_identity[0] or (
            installed_identity[1] != installed_modes.get(installed, 0o644)
        ):
            drift = True
    for old in args.absent:
        if not Path(old).is_absolute():
            raise Unknown(f"retired path must be absolute: {old}")
        drift |= absent_state(Path(old))
    for unit, expected in args.unit_enabled:
        if unit in missing_units:
            drift = True
            continue
        rc, observed = systemd("is-enabled", unit)
        if observed == "masked" or observed == "masked-runtime":
            raise Unknown(f"unit masked by an independent owner: {unit}")
        known = {"enabled", "enabled-runtime", "disabled", "static", "indirect",
                 "alias", "linked", "linked-runtime", "not-found"}
        if observed not in known or rc not in (0, 1, 3, 4):
            raise Unknown(f"could not establish unit enablement: {unit}")
        if observed != expected:
            drift = True
    for unit in args.unit_loaded:
        if unit in missing_units:
            drift = True
            continue
        rc, observed = systemd("show", unit, "--property=NeedDaemonReload", "--value")
        if rc or observed not in {"no", "yes"}:
            raise Unknown(f"could not establish unit loaded state: {unit}")
        if observed == "yes":
            drift = True
    return "DRIFT" if drift else "MATCH"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", nargs=2, action="append", default=[],
                        metavar=("SOURCE", "INSTALLED"))
    parser.add_argument("--glob", nargs=2, action="append", default=[],
                        metavar=("SOURCE_GLOB", "INSTALLED_DIR"))
    parser.add_argument("--absent", action="append", default=[], metavar="RETIRED_FILE")
    parser.add_argument("--mode", nargs=2, action="append", default=[],
                        metavar=("INSTALLED_FILE", "OCTAL_MODE"))
    parser.add_argument("--unit-enabled", nargs=2, action="append", default=[],
                        metavar=("UNIT", "EXPECTED"))
    parser.add_argument("--unit-loaded", action="append", default=[], metavar="UNIT")
    args = parser.parse_args(argv)
    try:
        print(classify(args))
    except Unknown as exc:
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
