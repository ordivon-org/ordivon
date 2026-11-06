"""Public execution coordinator composing effects and owner readback without new authority."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .execution_commands import ExecutionCommandMethods
from .execution_observations import ExecutionObservationMethods
from .routing import CapabilityRoute
from .upstream import OwnerToolCaller

if TYPE_CHECKING:
    from .external_worker import ExternalPullWorkerTransport


class ExecutionCoordinator(ExecutionCommandMethods, ExecutionObservationMethods):
    """Expose existing Gateway execution surface; natural owners keep durable truth."""

    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute],
        external_workers: ExternalPullWorkerTransport | None,
    ) -> None:
        self._caller = caller
        self._routes = routes
        self._external_workers = external_workers
