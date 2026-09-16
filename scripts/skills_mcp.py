#!/usr/bin/env python3
"""Read-only federated Agent Skills MCP service for Ordivon."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import json
import os
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from mcp.server import MCPServer
from mcp.server.extension import Extension, MethodBinding
from mcp.server.caching import CacheHint
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_PARAMS, CallToolResult, RequestParams, TextContent, ToolAnnotations

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("ORDIVON_SKILLS_MCP_SOURCE_ROOT", str(DEFAULT_SOURCE_ROOT))).resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ordivon_harness.skills import (  # noqa: E402
    SkillCatalog,
    SkillCatalogError,
    SkillContext,
)
from ordivon_harness.skills.config import load_skills_mcp_config  # noqa: E402
from ordivon_harness.skills.sep2640 import (  # noqa: E402
    AgentSkillsConformanceError,
    manifest_contains,
    parse_skill_uri,
    skill_entry,
    skill_uri,
)

DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8895
DEFAULT_CONFIG = Path("/etc/ordivon/skills-mcp.json")
DEFAULT_TOKEN = Path("/etc/ordivon/skills-mcp.token")
DEFAULT_BODY_LIMIT = 1_048_576


@dataclass(frozen=True, slots=True)
class McpSettings:
    config_file: Path
    token_file: Path = DEFAULT_TOKEN
    bind_host: str = DEFAULT_BIND
    port: int = DEFAULT_PORT
    body_limit_bytes: int = DEFAULT_BODY_LIMIT
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if not self.config_file.is_absolute() or not self.token_file.is_absolute():
            raise ValueError("config/token paths must be absolute")
        if self.bind_host not in {"127.0.0.1", "::1"}:
            raise ValueError("Skills MCP must bind literal loopback only")
        if type(self.port) is not int or not (1 <= self.port <= 65535):
            raise ValueError("port must be in [1,65535]")
        if type(self.body_limit_bytes) is not int or self.body_limit_bytes < 1:
            raise ValueError("body limit must be positive")

    @property
    def endpoint(self) -> str:
        host = f"[{self.bind_host}]" if ":" in self.bind_host else self.bind_host
        return f"http://{host}:{self.port}/mcp"


class CatalogProvider:
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self._catalog: SkillCatalog | None = None
        self._deadline = 0.0
        self._ttl_ms = 0
        self._workspace_roots: dict[str, Path] = {}

    def get(self, *, force_refresh: bool = False) -> SkillCatalog:
        now = time.monotonic()
        if self._catalog is not None and not force_refresh and now < self._deadline:
            return self._catalog
        cfg = load_skills_mcp_config(self.config_file)
        catalog = SkillCatalog.scan(cfg.sources)
        self._catalog = catalog
        self._workspace_roots = dict(cfg.workspaces)
        self._ttl_ms = cfg.ttl_ms
        self._deadline = now + cfg.ttl_ms / 1000.0
        return catalog

    @property
    def ttl_ms(self) -> int:
        return self._ttl_ms

    def context(self, workspace_id: str | None, agent_id: str | None) -> SkillContext | None:
        if workspace_id is None and agent_id is None:
            return None
        path = None
        if workspace_id is not None:
            if workspace_id not in self._workspace_roots:
                raise ValueError(f"unknown pre-registered workspaceId: {workspace_id}")
            path = self._workspace_roots[workspace_id]
        return SkillContext(workspace_path=path, workspace_id=workspace_id, agent_id=agent_id)


def _read_token(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("Skills MCP token must be one regular non-symlink file")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise RuntimeError("Skills MCP token file must have no group/other permission bits")
    token = path.read_text(encoding="utf-8").strip()
    if len(token) < 32 or any(ch.isspace() for ch in token):
        raise RuntimeError("Skills MCP token must be at least 32 non-whitespace characters")
    return token


def _result(value: dict[str, Any], *, error: bool = False) -> CallToolResult:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return CallToolResult(
        content=[TextContent(type="text", text=raw)],
        structuredContent=value,
        isError=error,
    )


def _error(error: Exception) -> CallToolResult:
    if isinstance(error, SkillCatalogError):
        return _result({"code": error.code, "detail": error.detail[:1000]}, error=True)
    return _result({"code": "INVALID_ARGUMENT", "detail": str(error)[:1000]}, error=True)


class SkillsListParams(RequestParams):
    cursor: str | None = None


class SkillsGetParams(RequestParams):
    uri: str


class Sep2640SkillsExtension(Extension):
    """Standard Agent Skills transport binding from SEP-2640.

    The legacy Ordivon tools remain a compatibility shim during migration; this
    extension is the canonical external Skills protocol.
    """

    identifier = "io.modelcontextprotocol/skills"
    _PAGE_SIZE = 100

    def __init__(self, provider: CatalogProvider) -> None:
        self.provider = provider

    def settings(self) -> dict[str, Any]:
        # resources/directory/read is optional and intentionally not advertised yet.
        return {}

    def methods(self) -> tuple[MethodBinding, ...]:
        versions = frozenset({"2026-07-28"})
        return (
            MethodBinding("skills/list", SkillsListParams, self._list, versions),
            MethodBinding("skills/get", SkillsGetParams, self._get, versions),
        )

    def _exportable_entries(self):
        catalog = self.provider.get()
        view = catalog.view(context=None, invocation_mode="implicit")
        entries = []
        for record in view.records:
            try:
                entries.append(skill_entry(record))
            except AgentSkillsConformanceError:
                # Dialect/nonconforming Skills stay in the internal raw catalog but
                # are never misrepresented as Agent Skills on the standard wire.
                continue
        entries.sort(key=lambda item: item.uri)
        return catalog, entries

    async def _list(self, _ctx, params: SkillsListParams) -> dict[str, Any]:
        catalog, entries = self._exportable_entries()
        offset = 0
        if params.cursor is not None:
            try:
                revision, raw_offset = params.cursor.rsplit(":", 1)
                offset = int(raw_offset)
            except (ValueError, TypeError) as exc:
                raise MCPError(INVALID_PARAMS, "invalid skills/list cursor") from exc
            if revision != catalog.catalog_revision or offset < 0:
                raise MCPError(INVALID_PARAMS, "stale or invalid skills/list cursor")
        page = entries[offset : offset + self._PAGE_SIZE]
        result: dict[str, Any] = {
            "resultType": "complete",
            "skills": [entry.value() for entry in page],
            "ttlMs": self.provider.ttl_ms,
            "cacheScope": "private",
        }
        next_offset = offset + len(page)
        if next_offset < len(entries):
            result["nextCursor"] = f"{catalog.catalog_revision}:{next_offset}"
        return result

    async def _get(self, _ctx, params: SkillsGetParams) -> dict[str, Any]:
        try:
            source_id, skill_name, relative_path = parse_skill_uri(params.uri)
            if relative_path != "SKILL.md":
                raise AgentSkillsConformanceError("skills/get URI must name SKILL.md")
            catalog = self.provider.get()
            record = catalog.by_skill_id(
                f"{source_id}/{skill_name}", invocation_mode="explicit"
            )
            if record.scope in {"project", "workspace"}:
                raise AgentSkillsConformanceError(
                    "project/workspace Skills require server-bound workspace context"
                )
            entry = skill_entry(record)
            if entry.uri != params.uri:
                raise AgentSkillsConformanceError("URI does not identify the served Skill")
        except (AgentSkillsConformanceError, SkillCatalogError, OSError) as exc:
            raise MCPError(INVALID_PARAMS, f"Skill is not served by the SEP-2640 surface: {exc}") from exc
        return {"resultType": "complete", "skill": entry.value()}


def build_server(provider: CatalogProvider) -> MCPServer:
    # Prime once so config/source errors fail during startup/check rather than first user turn.
    provider.get(force_refresh=True)
    server = MCPServer(
        name="ordivon-skills-mcp",
        title="Ordivon Skills",
        description="Read-only cross-harness Agent Skills discovery, resolution, and exact revision-bound resource projection.",
        instructions=(
            "Use skills.search/list for metadata discovery, skills.resolve for one exact binding, and skills.read to activate only the needed instructions/resources. "
            "This service never installs, mutates, trusts, or executes Skills. Runtime/providers retain execution authority."
        ),
        version="2",
        cache_hints={
            "resources/list": CacheHint(ttl_ms=30_000, scope="private"),
            "resources/read": CacheHint(ttl_ms=30_000, scope="private"),
        },
        extensions=[Sep2640SkillsExtension(provider)],
    )
    annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )

    @server.tool(
        name="skills.list",
        title="List available Skills",
        description="List lightweight model-visible Skill metadata only; blocked/untrusted Skill descriptions are never returned.",
        annotations=annotations,
    )
    async def skills_list(
        sourceId: str | None = None,
        scope: str | None = None,
        workspaceId: str | None = None,
        agentId: str | None = None,
        forceRefresh: bool = False,
        cursor: int = 0,
        limit: int = 100,
    ) -> CallToolResult:
        try:
            if cursor < 0 or not (1 <= limit <= 100):
                raise ValueError("cursor must be non-negative and limit in [1,100]")
            catalog = provider.get(force_refresh=forceRefresh)
            context = provider.context(workspaceId, agentId)
            view = catalog.view(context=context, invocation_mode="implicit")
            rows = list(view.records)
            if sourceId is not None:
                rows = [row for row in rows if row.source_id == sourceId]
            if scope is not None:
                rows = [row for row in rows if row.scope == scope]
            page = rows[cursor : cursor + limit]
            value: dict[str, Any] = {
                "catalogRevision": catalog.catalog_revision,
                "snapshotRevision": view.snapshot_revision,
                "ttlMs": provider.ttl_ms,
                "skills": [row.metadata() for row in page],
                "sources": [
                    {
                        "sourceId": status.source_id,
                        "health": status.health.value,
                        "discovered": status.discovered,
                        "valid": status.valid,
                        "invalid": status.invalid,
                        "quarantined": status.quarantined,
                        "admitted": status.admitted,
                    }
                    for status in catalog.source_statuses
                ],
            }
            if cursor + len(page) < len(rows):
                value["nextCursor"] = cursor + len(page)
            return _result(value)
        except (SkillCatalogError, ValueError, OSError, json.JSONDecodeError) as exc:
            return _error(exc)

    @server.tool(
        name="skills.search",
        title="Search available Skills",
        description="Search model-visible metadata; this ranks candidates but does not execute or force-select a Skill.",
        annotations=annotations,
    )
    async def skills_search(
        query: str,
        workspaceId: str | None = None,
        agentId: str | None = None,
        forceRefresh: bool = False,
        limit: int = 20,
    ) -> CallToolResult:
        try:
            if not query.strip() or not (1 <= limit <= 20):
                raise ValueError("query must be nonblank and limit in [1,20]")
            catalog = provider.get(force_refresh=forceRefresh)
            context = provider.context(workspaceId, agentId)
            view = catalog.view(context=context, invocation_mode="implicit")
            rows = catalog.search(query, context=context, invocation_mode="implicit", limit=limit)
            return _result(
                {
                    "catalogRevision": catalog.catalog_revision,
                    "snapshotRevision": view.snapshot_revision,
                    "skills": [row.metadata() for row in rows],
                }
            )
        except (SkillCatalogError, ValueError, OSError, json.JSONDecodeError) as exc:
            return _error(exc)

    @server.tool(
        name="skills.resolve",
        title="Resolve one Skill",
        description="Resolve a canonical skillId or friendly name to one exact current binding; ambiguity and stale snapshots fail closed.",
        annotations=annotations,
    )
    async def skills_resolve(
        ref: str,
        invocationMode: Literal["explicit", "implicit"] = "explicit",
        workspaceId: str | None = None,
        agentId: str | None = None,
        expectedSnapshotRevision: str | None = None,
        forceRefresh: bool = False,
    ) -> CallToolResult:
        try:
            catalog = provider.get(force_refresh=forceRefresh)
            context = provider.context(workspaceId, agentId)
            resolution = catalog.resolve(
                ref,
                context=context,
                invocation_mode=invocationMode,
                expected_snapshot_revision=expectedSnapshotRevision,
            )
            row = resolution.resolved
            package_hex = row.package_revision.removeprefix("sha256:")
            resource_uri = None
            if row.scope not in {"project", "workspace"}:
                resource_uri = f"skill://{row.source_id}/{row.name}/{package_hex}/SKILL.md"
            value = {
                "resolved": row.metadata(),
                "resolutionReason": resolution.reason,
                "shadowed": [item.metadata() for item in resolution.shadowed],
                "snapshotRevision": resolution.snapshot_revision,
                "mainResourceUri": resource_uri,
            }
            return _result(value)
        except (SkillCatalogError, ValueError, OSError, json.JSONDecodeError) as exc:
            return _error(exc)

    @server.tool(
        name="skills.read",
        title="Read one Skill resource",
        description="Read exact Skill text under snapshot, instruction, and package revision fences. Never executes scripts.",
        annotations=annotations,
    )
    async def skills_read(
        skillId: str,
        path: str = "SKILL.md",
        workspaceId: str | None = None,
        agentId: str | None = None,
        expectedInstructionDigest: str | None = None,
        expectedPackageRevision: str | None = None,
        expectedSnapshotRevision: str | None = None,
        offset: int = 0,
        maxBytes: int = 1_048_576,
    ) -> CallToolResult:
        try:
            catalog = provider.get()
            context = provider.context(workspaceId, agentId)
            result = catalog.read_text(
                skillId,
                relative_path=path,
                context=context,
                expected_instruction_digest=expectedInstructionDigest,
                expected_package_revision=expectedPackageRevision,
                expected_snapshot_revision=expectedSnapshotRevision,
                offset=offset,
                max_bytes=maxBytes,
            )
            return _result(result.value())
        except (SkillCatalogError, ValueError, OSError, json.JSONDecodeError) as exc:
            return _error(exc)

    @server.resource(
        "skill://ordivon/{sourceId}/{skillName}/{+path}",
        name="agent-skill-resource",
        title="SEP-2640 Agent Skill resource",
        description="Standards-conforming Agent Skill file exposed through MCP resources/read.",
        mime_type="text/plain",
    )
    def standard_skill_resource(sourceId: str, skillName: str, path: str) -> str | bytes:
        catalog = provider.get()
        try:
            record = catalog.by_skill_id(
                f"{sourceId}/{skillName}", invocation_mode="explicit"
            )
            if record.scope in {"project", "workspace"}:
                raise AgentSkillsConformanceError(
                    "project/workspace Skills require server-bound workspace context"
                )
            entry = skill_entry(record)
            requested_uri = skill_uri(sourceId, skillName, path)
            if not manifest_contains(entry, requested_uri):
                raise AgentSkillsConformanceError(
                    "resource is not present in the advertised Skill manifest"
                )
            target = (record.skill_root / path).resolve(strict=True)
            root = record.skill_root.resolve(strict=True)
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise AgentSkillsConformanceError("resource path escapes Skill root") from exc
            data = target.read_bytes()
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data
        except (AgentSkillsConformanceError, SkillCatalogError, OSError) as exc:
            raise ValueError(f"SEP2640_RESOURCE_ERROR: {exc}") from exc

    @server.resource(
        "skill://{sourceId}/{skillName}/{packageHex}/{+path}",
        name="skill-resource",
        title="Revision-bound Skill resource",
        description="Read a non-project Skill resource only when its exact package revision is still current.",
        mime_type="text/plain",
    )
    def skill_resource(sourceId: str, skillName: str, packageHex: str, path: str) -> str:
        catalog = provider.get()
        skill_id = f"{sourceId}/{skillName}"
        record = catalog.by_skill_id(skill_id, invocation_mode="explicit")
        if record.scope in {"project", "workspace"}:
            raise ValueError("RESOURCE_CONTEXT_REQUIRED: project/workspace Skills must use skills.read with context")
        expected = "sha256:" + packageHex
        if record.package_revision != expected:
            raise ValueError("PACKAGE_CHANGED: resource URI package revision is stale")
        try:
            return catalog.read_text(
                skill_id,
                relative_path=path,
                expected_package_revision=expected,
            ).content
        except SkillCatalogError as exc:
            raise ValueError(f"{exc.code}: {exc.detail}") from exc

    return server


async def _drain(receive, *, max_bytes: int) -> bool:
    total = 0
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            return True
        if message.get("type") != "http.request":
            continue
        body = message.get("body", b"")
        if not isinstance(body, bytes):
            return False
        total += len(body)
        if total > max_bytes:
            return False
        if message.get("more_body") is not True:
            return True


async def _problem(send, status: int, detail: str, *, authenticate: bool = False) -> None:
    value = {"type": "about:blank", "status": status, "detail": detail[:1000]}
    raw = json.dumps(value, separators=(",", ":")).encode()
    headers = [(b"content-type", b"application/problem+json"), (b"content-length", str(len(raw)).encode())]
    if authenticate:
        headers.append((b"www-authenticate", b"Bearer"))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": raw})


class BearerAuthApp:
    def __init__(self, app, token: str, *, body_limit_bytes: int) -> None:
        self.app = app
        self.expected = f"Bearer {token}".encode()
        self.body_limit_bytes = body_limit_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        authorization = b""
        for name, value in scope.get("headers", []):
            if name.lower() == b"authorization":
                authorization = value
                break
        if not hmac.compare_digest(authorization, self.expected):
            if not await _drain(receive, max_bytes=self.body_limit_bytes):
                return await _problem(send, 413, "request body exceeds configured limit")
            return await _problem(send, 401, "valid Bearer credential required", authenticate=True)
        return await self.app(scope, receive, send)


def _transport_security() -> TransportSecuritySettings:
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
    )


def build_app(settings: McpSettings, provider: CatalogProvider, token: str):
    server = build_server(provider)
    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=settings.body_limit_bytes,
        transport_security=_transport_security(),
        host=settings.bind_host,
    )
    return BearerAuthApp(app, token, body_limit_bytes=settings.body_limit_bytes)


def run_http(settings: McpSettings, provider: CatalogProvider) -> None:
    token = _read_token(settings.token_file)
    app = build_app(settings, provider, token)
    import uvicorn

    uvicorn.run(
        app,
        host=settings.bind_host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=False,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN)
    parser.add_argument("--bind", default=DEFAULT_BIND)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--body-limit-bytes", type=int, default=DEFAULT_BODY_LIMIT)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--transport", choices=["http", "stdio"], default="http")
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    settings = McpSettings(
        config_file=args.config.resolve(),
        token_file=args.token_file.resolve(),
        bind_host=args.bind,
        port=args.port,
        body_limit_bytes=args.body_limit_bytes,
        log_level=args.log_level.upper(),
    )
    provider = CatalogProvider(settings.config_file)
    server = build_server(provider)
    if args.check:
        catalog = provider.get()
        tools = sorted(tool.name for tool in server._tool_manager.list_tools())
        standard_exportable = 0
        standard_rejected = 0
        for record in catalog.view(context=None, invocation_mode="implicit").records:
            try:
                skill_entry(record)
            except AgentSkillsConformanceError:
                standard_rejected += 1
            else:
                standard_exportable += 1
        print(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ordivon.skills-mcp-check",
                    "status": "ok",
                    "endpoint": settings.endpoint,
                    "toolNames": tools,
                    "toolCount": len(tools),
                    "catalogRevision": catalog.catalog_revision,
                    "standards": {
                        "packageFormat": "Agent Skills",
                        "mcpExtension": "io.modelcontextprotocol/skills",
                        "protocolMethods": ["skills/get", "skills/list", "resources/read"],
                        "directoryRead": False,
                        "standardExportable": standard_exportable,
                        "standardRejected": standard_rejected,
                        "legacyToolShim": True,
                    },
                    "sources": [
                        {
                            "sourceId": status.source_id,
                            "health": status.health.value,
                            "valid": status.valid,
                            "invalid": status.invalid,
                            "quarantined": status.quarantined,
                        }
                        for status in catalog.source_statuses
                    ],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.transport == "stdio":
        asyncio.run(server.run_stdio_async())
        return 0
    run_http(settings, provider)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
