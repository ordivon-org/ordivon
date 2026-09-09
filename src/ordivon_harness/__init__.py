"""Ordivon Harness public API.

The package root is the same caller-neutral, Host-free surface as ``ordivon_harness.api``.
Higher-level orchestration integrates through this caller-neutral surface rather than a
Host-specific compatibility adapter.
"""

from .api import *  # noqa: F403
from .api import __all__ as _API_ALL
from .version import package_version

__all__ = [*_API_ALL, "package_version"]
