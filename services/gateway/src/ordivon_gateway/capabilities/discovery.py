from __future__ import annotations

import asyncio
from importlib.metadata import version as package_version

from ..contracts import (
    CapabilityDescriptor,
    CapabilityInquiryProjection,
    CapabilityProjection,
    CapabilityResolution,
    CapabilityRoute,
    CapabilitySearchProjection,
    SystemDescription,
)
from ..logic.capability_projection import (
    candidate_routes_for_search,
    project_capability_search,
    project_execution_capability,
    project_native_release_capability,
)
from ..logic.catalog_identity import project_system_description, route_digest
from ..logic.catalog_projection import (
    assemble_catalog_projection,
    project_artifact_capability,
    project_host_capability,
    project_static_capability,
)
from ..logic.execution_refs import GatewayError
from ..logic.host_tool_contracts import host_read_transport_route
from ..logic.owner_protocol import OwnerToolCaller, _configuration_error, _configured
from ..logic.readiness_confirmation import (
    annotate_unclassified_payload_drift,
    compare_readiness_observations,
    status_probe_owners,
)
from .owner_observation import OwnerStatusObserver
from .research import resolve_research_capability


class CapabilityCatalog:
    """Read-only capability discovery and composition resolution over natural owners.

    This catalog observes owners but never owns their execution, state or completion.
    The GatewayService API is a compatibility façade over this boundary.
    """

    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute],
        projection_timeout_seconds: float,
    ) -> None:
        self._caller = caller
        self._routes = routes
        self._projection_timeout_seconds = projection_timeout_seconds
        self._route_digest = route_digest(routes)

    def system_describe(self) -> SystemDescription:
        # Endpoint configuration is observed here; the identity projection is pure.
        configs = {
            owner_id: _configured(self._caller, owner_id)
            for owner_id in ("runtime.linux", "runtime.windows", "runtime.harness")
        }
        configs["host"] = _configured(self._caller, "host") or (
            host_read_transport_route(self._caller) == "host.read"
            and _configured(self._caller, "host.read")
        )
        configs["skills"] = _configured(self._caller, "skills")
        configs["research.composition"] = True
        return project_system_description(
            self._routes,
            gateway_version=package_version("ordivon-gateway"),
            route_identity=self._route_digest,
            owner_configured=configs,
        )

    async def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        # Discovery and dispatch share the same natural-owner route table.
        if capability is not None:
            route = self._routes.get(capability)
            if route is None:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route]
        else:
            selected = [self._routes[key] for key in sorted(self._routes)]
        return await self._describe_routes(selected)

    async def _describe_routes(self, selected: list[CapabilityRoute]) -> CapabilityProjection:
        # A search can restrict observations to matching routes before any I/O.
        # Normalize order independently from search ranking for stable digests.
        selected = sorted(selected, key=lambda route: route.capability)
        # One observation context per describe request: no global status cache.
        observer = OwnerStatusObserver(self._caller, self._projection_timeout_seconds)
        runtime_description = observer.runtime_description

        async def execution_descriptor(route: CapabilityRoute) -> CapabilityDescriptor:
            configured = _configured(self._caller, route.owner_id)
            if not configured:
                return project_execution_capability(
                    route,
                    configured_at_gateway=False,
                    owner_response=None,
                    configuration_error=_configuration_error(self._caller, route.owner_id),
                )
            response, error = await runtime_description(route.owner_id)
            return project_execution_capability(
                route,
                configured_at_gateway=True,
                owner_response=response,
                observation_error=error,
            )

        # Only independent read-only observations fan out. TaskGroup keeps child
        # lifetimes inside this request; no cross-request cache or effect retry.
        runtime_owners = {
            route.owner_id for route in selected if route.category in {"execution", "release"}
        }
        if any(route.capability == "artifact.runtime" for route in selected):
            runtime_owners.update(("runtime.linux", "runtime.windows"))
        host_probe = None
        host_status_route = host_read_transport_route(self._caller)
        async with asyncio.TaskGroup() as probes:
            for owner_id in sorted(runtime_owners):
                probes.create_task(runtime_description(owner_id))
            if any(route.capability == "continuity.external" for route in selected) and _configured(
                self._caller, host_status_route
            ):
                host_probe = probes.create_task(
                    observer.observe(host_status_route, "host.status", {"detail": "summary"})
                )

        values: list[CapabilityDescriptor] = []
        for route in selected:
            if route.category == "execution":
                values.append(await execution_descriptor(route))
                continue

            if route.category == "release":
                owner_configured = _configured(self._caller, route.owner_id)
                response, error = (
                    await runtime_description(route.owner_id) if owner_configured else (None, None)
                )
                values.append(
                    project_native_release_capability(
                        route,
                        configured_at_gateway=owner_configured,
                        owner_response=response,
                        observation_error=error,
                        configuration_error=_configuration_error(self._caller, route.owner_id)
                        if not owner_configured
                        else None,
                    )
                )
                continue

            if route.category == "research":
                values.append(project_static_capability(route))
                continue

            if route.capability == "continuity.external":
                configured = _configured(self._caller, host_status_route)
                result, error = host_probe.result() if host_probe is not None else (None, None)
                values.append(
                    project_host_capability(
                        route, configured=configured, result=result, error=error
                    )
                )
                continue

            if route.capability == "artifact.runtime":
                observations = []
                for owner_id in ("runtime.linux", "runtime.windows"):
                    configured = _configured(self._caller, owner_id)
                    result, error = (
                        await runtime_description(owner_id)
                        if configured
                        else (None, _configuration_error(self._caller, owner_id))
                    )
                    observations.append((owner_id, configured, result, error))
                values.append(project_artifact_capability(route, observations=observations))
                continue

            values.append(project_static_capability(route))

        # The one request-scoped observation cache is also the input to a
        # falsifiable inquiry: do not rerun Owner calls or replace UNKNOWN with
        # a guessed negative. Store distinct per-Owner evidence on each result.
        observed_owner_status = dict(observer.runtime_cache)
        if host_probe is not None:
            observed_owner_status["host"] = host_probe.result()
        owner_configs = {
            owner_id: (
                _configured(self._caller, owner_id),
                _configuration_error(self._caller, owner_id),
            )
            for owner_id in (
                "runtime.linux",
                "runtime.windows",
                "runtime.harness",
                "host",
                "host.read",
                "skills",
            )
        }
        # "host" is a natural Owner; "host.read" is merely an optional
        # transport alias, not a new semantic truth or Security Principal.
        owner_configs["host.write"] = owner_configs["host"]
        if host_status_route == "host.read":
            owner_configs["host"] = owner_configs["host.read"]
        return assemble_catalog_projection(
            values,
            self._routes,
            route_identity=self._route_digest,
            owner_configurations=owner_configs,
            owner_observations=observed_owner_status,
        )

    async def capability_inquire(
        self, *, capability: str, verify_read_only: bool = False
    ) -> CapabilityInquiryProjection:
        """Explicit one-extra-observation option, no effect calls or background retries."""
        if type(verify_read_only) is not bool:
            raise GatewayError("verifyReadOnly must be a JSON boolean")
        route = self._routes.get(capability)
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")

        async def once() -> CapabilityInquiryProjection:
            projection = await self.capability_describe(capability)
            descriptor = projection.capabilities[0]
            inquiry = descriptor._readiness_inquiry
            if inquiry is None:
                raise GatewayError("Gateway readiness inquiry was not assembled")
            return CapabilityInquiryProjection(
                capability=descriptor.capability,
                owner_id=descriptor.owner_id,
                readiness_state=descriptor.readiness_state,
                route_digest=projection.route_digest,
                projection_digest=projection.projection_digest,
                inquiry=inquiry,
            )

        initial = await once()
        if not verify_read_only:
            return initial
        # Research is pure static route metadata. A second look at that same
        # object is NOT an independent Owner observation or an information gain.
        if not status_probe_owners(route.category, route.owner_id):
            return initial.model_copy(
                update={
                    "verification": compare_readiness_observations(
                        category=route.category,
                        owner_id=route.owner_id,
                        initial=initial,
                        latest=initial,
                    )
                }
            )
        # Never retry a submission, receipt, Artifact read, Host write or
        # policy grant: only the existing read-only describe/status observation.
        latest = await once()
        verification = compare_readiness_observations(
            category=route.category,
            owner_id=route.owner_id,
            initial=initial,
            latest=latest,
        )
        return latest.model_copy(
            update={
                "verification": verification,
                "inquiry": annotate_unclassified_payload_drift(latest.inquiry, verification),
            }
        )

    async def capability_search(
        self,
        *,
        query: str,
        category: str | None = None,
        owner_id: str | None = None,
        limit: int = 10,
        include_unavailable: bool = True,
    ) -> CapabilitySearchProjection:
        if not isinstance(query, str) or query != query.strip() or not query:
            raise GatewayError("query must be non-empty trimmed text")
        if len(query) > 512:
            raise GatewayError("query exceeds 512 characters")
        if category is not None and (
            not isinstance(category, str) or category != category.strip() or not category
        ):
            raise GatewayError("category must be non-empty trimmed text when provided")
        if owner_id is not None and (
            not isinstance(owner_id, str) or owner_id != owner_id.strip() or not owner_id
        ):
            raise GatewayError("ownerId must be non-empty trimmed text when provided")
        if type(limit) is not int or not 1 <= limit <= 50:
            raise GatewayError("limit must be an integer between 1 and 50")
        if type(include_unavailable) is not bool:
            raise GatewayError("includeUnavailable must be boolean")

        # Find candidates from immutable routing metadata before any Owner RPC.
        # A miss (or a Research-only match) cannot be delayed by unrelated
        # Windows/Host observations. Filtering on real availability still occurs
        # AFTER observing every matching route, so UNKNOWN is never guessed FALSE.
        candidates = candidate_routes_for_search(
            self._routes,
            query=query,
            category=category,
            owner_id=owner_id,
        )
        projection = await self._describe_routes(candidates)
        return project_capability_search(
            projection,
            query=query,
            category=category,
            owner_id=owner_id,
            limit=limit,
            include_unavailable=include_unavailable,
        )

    async def capability_resolve(
        self,
        *,
        capability: str,
        workspace_id: str | None = None,
        agent_id: str | None = None,
    ) -> CapabilityResolution:
        return await resolve_research_capability(
            self._caller,
            self._routes,
            capability=capability,
            workspace_id=workspace_id,
            agent_id=agent_id,
        )
