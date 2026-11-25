"""Owner-local Linux snapshot source inode binding, shared by backup and restore."""

from __future__ import annotations

import ctypes
import errno
import os
import stat
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path


@contextmanager
def pinned_source_entry(source: Path, relative: Path):
    """Pin Linux snapshot components with native openat no-follow resolution.

    This is narrower than openat2: no cross-mount exclusion is asserted, and
    other platforms retain their existing static/staging checks.
    """
    if not sys.platform.startswith("linux"):
        yield source / relative
        return
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    with ExitStack() as stack:
        parent_fd = os.open(source, flags | os.O_DIRECTORY)
        stack.callback(os.close, parent_fd)
        for segment in relative.parts[:-1]:
            parent_fd = os.open(segment, flags | os.O_DIRECTORY, dir_fd=parent_fd)
            stack.callback(os.close, parent_fd)
        file_fd = os.open(relative.name, flags, dir_fd=parent_fd)
        stack.callback(os.close, file_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise ValueError(f"snapshot entry is not a regular file: {relative}")
        # copy2 retains the original mode/timestamps while all data and
        # metadata reads use the pinned descriptor, not a raceable pathname.
        yield Path("/proc/self/fd") / str(file_fd)


def publish_new_directory(staging: Path, destination: Path) -> None:
    """Publish a new snapshot or restore atomically, never replacing another owner.

    The earlier destination.exists() check is only a preflight, not a
    concurrency fence. Linux uses the kernel RENAME_NOREPLACE primitive.
    """
    if sys.platform.startswith("linux"):
        try:
            renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
        except AttributeError as error:
            raise OSError(errno.ENOSYS, "atomic no-replace rename unavailable") from error
        renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        renameat2.restype = ctypes.c_int
        # Native Linux ABI: AT_FDCWD=-100, RENAME_NOREPLACE=1.
        if renameat2(-100, os.fsencode(staging), -100, os.fsencode(destination), 1) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), str(destination))
    elif os.name == "nt":
        # Windows os.rename fails if the target already exists.
        os.rename(staging, destination)
    else:
        raise OSError(errno.ENOSYS, "atomic no-replace directory publication unavailable")
