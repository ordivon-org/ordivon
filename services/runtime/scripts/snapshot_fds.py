"""Owner-local Linux snapshot source inode binding, shared by backup and restore."""

from __future__ import annotations

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
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
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
