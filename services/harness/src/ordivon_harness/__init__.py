"""Ordivon Harness package identity.

Use :mod:`ordivon_harness.api` for the supported application facade. Import exact
owner submodules for advanced integrations. The package root deliberately does not
mirror the application API.
"""

from .version import package_version

__all__ = ["package_version"]
