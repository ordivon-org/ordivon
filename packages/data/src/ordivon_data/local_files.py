"""Scoped, descriptor-bound local-file SHA-256 for Data producer and consumer.

This is a small shared I/O boundary, not a second artifact store, publication
engine or security authorization layer. It observes one open file descriptor;
producer immutability and later consumer read-back are separate contracts.
"""

from __future__ import annotations

import errno
import hashlib
import os
import stat
from pathlib import Path

_SCOPED_OPEN_SUPPORTED = (
    os.open in os.supports_dir_fd
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
)


def scoped_sha256(
    path: Path, allowed_roots: tuple[Path, ...], *, hash_bytes: bool
) -> tuple[str | None, str]:
    """Hash one opened regular-file descriptor, anchored to an allowed root.

    Linux/POSIX openat-style dir_fd traversal + O_NOFOLLOW closes the
    check-then-open pathname race. Symlink components are intentionally not
    accepted, even when they currently resolve within an allowed root.
    A concurrent in-place writer is detected on best-effort file metadata;
    immutable producer snapshots remain required for strong read isolation.
    """
    if ".." in path.parts or "\x00" in str(path):
        return None, "unsupported_scoped_path"
    roots = sorted(
        (root.absolute() for root in allowed_roots if ".." not in root.parts),
        key=lambda root: len(root.parts),
        reverse=True,
    )
    matching = [root for root in roots if path.is_relative_to(root)]
    if not matching:
        return None, "outside_explicit_scope"
    if not _SCOPED_OPEN_SUPPORTED:
        # Never silently fall back to an unsafe path reopen on other OSes.
        return None, "scoped_descriptor_unavailable"

    dir_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    reason = "local_file_unavailable"
    for root in matching:
        relative = path.relative_to(root)
        if not relative.parts:
            return None, "unsupported_scoped_path"
        directory_fd = None
        try:
            directory_fd = os.open("/", dir_flags)
            # Anchor every ancestor, including the allowed root itself.
            # No pathname is consulted after its directory FD is opened.
            for component in (*root.parts[1:], *relative.parts[:-1]):
                next_fd = os.open(component, dir_flags, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            fd = os.open(relative.parts[-1], file_flags, dir_fd=directory_fd)
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode):
                    return None, "not_regular_file"
                if not hash_bytes:
                    return None, "sha256_not_bound"
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
                after = os.fstat(stream.fileno())
                identity = lambda st: (
                    st.st_dev,
                    st.st_ino,
                    st.st_size,
                    st.st_mtime_ns,
                    st.st_ctime_ns,
                )
                if identity(before) != identity(after):
                    return None, "file_changed_during_read"
                return digest, "descriptor_digest_observed"
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                reason = "unsupported_scoped_path"
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
    return None, reason
