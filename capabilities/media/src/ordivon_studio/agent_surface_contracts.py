"""Transport-independent Studio Agent tool contracts.

Discovery is source-only and must not import optional media provider,
production, equipment or creative-index implementations. Existing public
action names/JSON Schemas remain unchanged; this file is their single source.
"""

from __future__ import annotations

from typing import Any


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "studio_dependencies_status",
            "description": "Observe whether Studio JavaScript and core Python dependencies are exactly materialized in this Workspace. This never installs anything.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_dependencies_propose",
            "description": "Compile an explicit dependency-materialization proposal for one missing Studio capability. It does not execute the acquisition; ordinary execution must never acquire implicitly.",
            "inputSchema": {
                "type": "object",
                "properties": {"target": {"type": "string", "enum": ["js", "python"]}},
                "required": ["target"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_production_standing",
            "description": "Read the bounded owner-native Production index and whether Studio has established a unique current Production. This does not infer priority or invent current intent; when no current Production is grounded, caller/owner intent must select one before Production-specific work.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_production_context",
            "description": "Read one current Studio Production as a bounded owner-native context projection: intent, audiences, source bindings, Claims, Outputs, and mechanical source-binding relation. This does not render, edit, publish, or infer semantic currentness.",
            "inputSchema": {
                "type": "object",
                "properties": {"productionId": {"type": "string", "minLength": 1}},
                "required": ["productionId"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_learning_context",
            "description": "Hydrate scoped retained learning from real Studio Productions together with the current Creative Alpha holdout/OOS boundary and promotion path. This is read-only evidence for future production decisions, not a universal quality model or approval gate.",
            "inputSchema": {
                "type": "object",
                "properties": {"currentProductionId": {"type": "string", "minLength": 1}},
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_creative_index_query",
            "description": "Query the rebuildable Creative Index for one term and return matching entities plus their one-hop relations. The index is navigation/cache data pinned to source revisions; it is not source authority and does not infer current physical availability.",
            "inputSchema": {
                "type": "object",
                "properties": {"term": {"type": "string", "minLength": 1}},
                "required": ["term"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_processing_profiles",
            "description": "Discover source-owned FFprobe/FFmpeg/OTIO/timed-text processing profiles and exact adapter paths with content digests. This is a read-only LEGO catalog projection; external tool readiness and effect authority remain with Workstation/Runtime.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_processing_probe_plan",
            "description": "Compile an exact read-only Runtime proposal from an existing processing profile and adapter, both SHA-256 pinned by a previous Studio discovery. Does not execute, acquire tools or decide publication.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "profileId": {"type": "string", "minLength": 1},
                    "expectedProfileDigest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                    "expectedAdapterDigest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                    "inputPath": {"type": "string", "minLength": 1},
                    "evidenceDirectory": {"type": "string", "minLength": 1},
                },
                "required": ["profileId", "expectedProfileDigest", "expectedAdapterDigest", "inputPath", "evidenceDirectory"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_equipment_propose",
            "description": "Select freshly observed equipment for one exact Studio capability and compile a truthful operation proposal with readiness, blockers, exact physical plan, and owner-specific verification contract. This does not execute the effect.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string", "minLength": 1},
                    "equipmentId": {"type": "string", "minLength": 1},
                    "parameters": {"type": "object"},
                },
                "required": ["capability", "parameters"],
                "additionalProperties": False,
            },
        },
    ]


def surface_projection() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-agent-tool-surface",
        "truthRole": "studio-domain-semantic-actions",
        "domainId": "domain:ordivon-studio",
        "revision": "studio-agent-surface-processing-probe-plan-v1",
        "tools": tool_definitions(),
        "runtimeOwnsPhysicalExecution": True,
        "harnessMayAdmitSubsetOnly": True,
        "mcpRequired": False,
        "boundary": "Studio owns readiness, dependency and medium semantics. Harness may bind these definitions into a turn but does not gain Studio authority; Runtime remains the physical executor of compiled plans.",
    }
