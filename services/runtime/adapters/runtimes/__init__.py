"""Runtime adapters exposed through provider-neutral core contracts."""

from adapters.runtimes.factory import resolve_runtime

__all__ = ["resolve_runtime"]
