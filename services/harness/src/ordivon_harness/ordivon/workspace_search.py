"""Workspace search capability contract and bounded ripgrep result projection.

Pure Tool schema and result interpretation: no Runtime client, Journal or
dispatch authority. The Runtime bridge remains the existing effect owner adapter.
"""
from __future__ import annotations

import json

from anc_canonical import JsonValue, canonical_digest

from ..runtime_port import HarnessRuntimeClientError
from .model import AgentToolDefinition


SEARCH_WORKSPACE_DEFINITION = AgentToolDefinition(
    name="search_workspace",
    description=(
        "Search UTF-8 workspace text with bounded ripgrep JSON output. Submit one scalar "
        "query for the existing deep-search path, or 1..8 independent queries to share one "
        "physical observation Job while retaining per-query result/evidence identity. "
        "This operation is observation-only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "queries": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
                "maxItems": 8,
            },
            "relativePath": {"type": "string", "default": "."},
            "maxMatches": {
                "type": "integer",
                "minimum": 1,
                "maximum": 200,
                "default": 50,
            },
            "maxMatchesPerQuery": {
                "type": "integer",
                "minimum": 1,
                "maximum": 25,
                "default": 25,
            },
        },
        "oneOf": [
            {
                "required": ["query"],
                "not": {"required": ["queries"]},
            },
            {
                "required": ["queries"],
                "not": {"required": ["query"]},
            },
        ],
        "additionalProperties": False,
    },
)
INDEPENDENT_SEARCH_TOOL_SURFACE: dict[str, JsonValue] = {
    "schemaVersion": 1,
    "kind": "ordivon.independent-search-tool-surface",
    "tools": [SEARCH_WORKSPACE_DEFINITION.to_dict()],
}
INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST = canonical_digest(INDEPENDENT_SEARCH_TOOL_SURFACE)
INDEPENDENT_SEARCH_TOOL_GRANT: dict[str, JsonValue] = {
    "schemaVersion": 1,
    "kind": "ordivon.independent-search-tool-grant",
    "tools": ["search_workspace"],
    "runtimeOperations": ["workspace.exec"],
    "workspaceMutationAllowed": False,
}
INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST = canonical_digest(INDEPENDENT_SEARCH_TOOL_GRANT)


def normalize_search(
    structured: dict[str, JsonValue], *, queries: tuple[str, ...] | None = None
) -> None:
    stdout = structured.get("stdoutTail")

    def normalized_matches(lines: list[str], limit: int) -> list[dict[str, JsonValue]]:
        matches: list[dict[str, JsonValue]] = []
        for raw_line in lines:
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict) or event.get("type") != "match":
                continue
            data = event.get("data")
            if not isinstance(data, dict):
                continue
            path = data.get("path")
            line_value = data.get("lines")
            line_number = data.get("line_number")
            absolute_offset = data.get("absolute_offset")
            submatches = data.get("submatches")
            path_text = path.get("text") if isinstance(path, dict) else None
            line_text = line_value.get("text") if isinstance(line_value, dict) else None
            if (
                not isinstance(path_text, str)
                or type(line_number) is not int
                or type(absolute_offset) is not int
                or not isinstance(submatches, list)
            ):
                continue
            for submatch in submatches:
                if not isinstance(submatch, dict):
                    continue
                match_start = submatch.get("start")
                match_end = submatch.get("end")
                if type(match_start) is not int or type(match_end) is not int:
                    continue
                matches.append(
                    {
                        "relativePath": path_text,
                        "lineNumber": line_number,
                        "column": match_start + 1,
                        "byteOffset": absolute_offset + match_start,
                        "matchBytes": match_end - match_start,
                        "lineText": (
                            None if not isinstance(line_text, str) else line_text[:2_048]
                        ),
                    }
                )
                if len(matches) >= limit:
                    return matches
        return matches

    if queries is None:
        lines = stdout.splitlines() if isinstance(stdout, str) else []
        matches = normalized_matches(lines, 200)
        structured["matches"] = matches
        structured["matchCount"] = len(matches)
        structured["locationSemantics"] = (
            "Use match.byteOffset as a read slice offset; lineNumber and column "
            "are one-based display locations."
        )
        return

    if not isinstance(stdout, str):
        raise HarnessRuntimeClientError("batch search Runtime result omitted stdoutTail")
    prefix_marker = "@@ORDIVON_SEARCH_BATCH:"
    frames: list[list[str]] = [[] for _ in queries]
    result_codes: list[int | None] = [None for _ in queries]
    active: int | None = None
    expected_begin = 0
    for line in stdout.splitlines():
        if line.startswith(prefix_marker + "BEGIN\t"):
            try:
                index = int(line.split("\t", 1)[1])
            except (ValueError, IndexError) as error:
                raise HarnessRuntimeClientError(
                    "batch search begin marker is invalid"
                ) from error
            if active is not None or index != expected_begin or index >= len(queries):
                raise HarnessRuntimeClientError("batch search begin sequence differs")
            active = index
            continue
        if line.startswith(prefix_marker + "END\t"):
            parts = line.split("\t")
            if len(parts) != 3:
                raise HarnessRuntimeClientError("batch search end marker is invalid")
            try:
                index = int(parts[1])
                result_code = int(parts[2])
            except ValueError as error:
                raise HarnessRuntimeClientError("batch search end marker is invalid") from error
            if active != index or index != expected_begin or result_code < 0:
                raise HarnessRuntimeClientError("batch search end sequence differs")
            result_codes[index] = result_code
            active = None
            expected_begin += 1
            continue
        if active is not None:
            frames[active].append(line)
    if (
        active is not None
        or expected_begin != len(queries)
        or any(code is None for code in result_codes)
    ):
        raise HarnessRuntimeClientError("batch search framing is incomplete")

    query_results: list[dict[str, JsonValue]] = []
    flattened: list[dict[str, JsonValue]] = []
    stderr = structured.get("stderrTail")
    error_summary = stderr[:2_048] if isinstance(stderr, str) and stderr else None
    for index, query_value in enumerate(queries):
        code = result_codes[index]
        assert code is not None
        matches = normalized_matches(frames[index], 25)
        status = "matched" if code == 0 else "no_hits" if code == 1 else "error"
        result: dict[str, JsonValue] = {
            "query": query_value,
            "queryIndex": index,
            "status": status,
            "exitCode": code,
            "matches": matches,
            "matchCount": len(matches),
        }
        if status == "error" and error_summary is not None:
            result["errorSummary"] = error_summary
        query_results.append(result)
        for match in matches:
            flattened.append({**match, "query": query_value, "queryIndex": index})
    structured["queryResults"] = query_results
    structured["matches"] = flattened
    structured["matchCount"] = len(flattened)
    structured["batchSearch"] = True
    structured["locationSemantics"] = (
        "Use each queryResult match.byteOffset as a read slice offset; lineNumber and "
        "column are one-based display locations. queryResults preserve independent "
        "query evidence while one Runtime Job carries the physical observation."
    )
