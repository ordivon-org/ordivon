#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pprint
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INDEX = ROOT / "profiles/research/capability-index/research-capability-index-r1.json"
ROUTING = (
    ROOT
    / ".agents/skills/research-capability-routing/references/research-capability-routing-r1.json"
)
OUTPUT = ROOT / "services/gateway/src/ordivon_gateway/research_routes.py"


def canonical_digest(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_sources() -> tuple[dict[str, object], dict[str, object]]:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    if index.get("schemaVersion") != 1 or index.get("kind") != "ordivon.research-capability-index":
        raise SystemExit("Research capability index identity mismatch")
    if (
        routing.get("schemaVersion") != 1
        or routing.get("kind") != "ordivon.research-capability-routing-profile"
    ):
        raise SystemExit("Research routing profile identity mismatch")

    declared = set(routing["problemClasses"])
    for capability in index["capabilities"]:
        unknown = sorted(set(capability["routeProblemClasses"]) - declared)
        if unknown:
            raise SystemExit(
                f"{capability['capability']}: unknown route problem classes: {unknown}"
            )
    return index, routing


def project(index: dict[str, object], routing: dict[str, object]) -> list[dict[str, object]]:
    routes = routing["routes"]
    projected: list[dict[str, object]] = []
    for capability in index["capabilities"]:
        skills: list[str] = []
        for problem_class in capability["routeProblemClasses"]:
            matching = sorted(
                (
                    route
                    for route in routes
                    if problem_class in route["problemClasses"]
                    and route["providerClass"] == "skill"
                ),
                key=lambda route: (route["rank"], route["routeId"]),
            )
            for route in matching:
                ref = route["providerRef"]
                if ref not in skills:
                    skills.append(ref)

        recipes: list[dict[str, object]] = []
        if skills:
            recipes.append(
                {
                    "recipe_id": "skill-explicit",
                    "kind": "skill",
                    "owner_id": "skills",
                    "command": [],
                    "note": capability["skillResolutionNote"]
                    or "Resolve an exact current Skill binding before activation.",
                }
            )
        for recipe in capability["directInvocationRecipes"]:
            recipes.append(
                {
                    "recipe_id": recipe["recipeId"],
                    "kind": recipe["kind"],
                    "owner_id": recipe["ownerId"],
                    "command": recipe["command"],
                    "note": recipe["note"],
                }
            )

        projected.append(
            {
                "capability": capability["capability"],
                "description": capability["description"],
                "tags": capability["tags"],
                "semantic_owner": capability["semanticOwner"],
                "completion_owner": capability["completionOwner"],
                "study_types": capability["studyTypes"],
                "preferred_skills": skills,
                "invocation_recipes": recipes,
                "source_refs": capability["sourceRefs"],
                "execution_capability": capability["executionCapability"],
                "truth_boundary": capability["truthBoundary"],
            }
        )
    return projected


def render() -> str:
    index, routing = load_sources()
    material = pprint.pformat(project(index, routing), width=100, sort_dicts=True)
    return f"""# GENERATED FILE — DO NOT EDIT BY HAND.
# Source: profiles/research/capability-index/research-capability-index-r1.json
# Provider bindings: .agents/skills/research-capability-routing/references/research-capability-routing-r1.json
# indexDigest={canonical_digest(index)} routingProfileDigest={canonical_digest(routing)}
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvocationRecipeSpec:
    recipe_id: str
    kind: str
    owner_id: str
    command: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class ResearchCapabilitySpec:
    capability: str
    description: str
    tags: tuple[str, ...]
    semantic_owner: str
    completion_owner: str
    study_types: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    invocation_recipes: tuple[InvocationRecipeSpec, ...]
    source_refs: tuple[str, ...]
    execution_capability: str | None = None
    truth_boundary: str = ""


_PROJECTED = {material}


def research_capabilities() -> dict[str, ResearchCapabilitySpec]:
    values: list[ResearchCapabilitySpec] = []
    for item in _PROJECTED:
        recipes = tuple(
            InvocationRecipeSpec(**{{**recipe, "command": tuple(recipe["command"])}})
            for recipe in item["invocation_recipes"]
        )
        values.append(
            ResearchCapabilitySpec(
                capability=item["capability"],
                description=item["description"],
                tags=tuple(item["tags"]),
                semantic_owner=item["semantic_owner"],
                completion_owner=item["completion_owner"],
                study_types=tuple(item["study_types"]),
                preferred_skills=tuple(item["preferred_skills"]),
                invocation_recipes=recipes,
                source_refs=tuple(item["source_refs"]),
                execution_capability=item["execution_capability"],
                truth_boundary=item["truth_boundary"],
            )
        )
    return {{value.capability: value for value in values}}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit("generated Research Gateway projection is missing")
        index, routing = load_sources()
        current = OUTPUT.read_text(encoding="utf-8")
        markers = (
            f"indexDigest={canonical_digest(index)}",
            f"routingProfileDigest={canonical_digest(routing)}",
        )
        if any(marker not in current for marker in markers):
            raise SystemExit("generated Research Gateway projection source digests are stale")
        spec = importlib.util.spec_from_file_location("_ordivon_research_routes_check", OUTPUT)
        if spec is None or spec.loader is None:
            raise SystemExit("cannot load generated Research Gateway projection")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        if module._PROJECTED != project(index, routing):
            raise SystemExit("generated Research Gateway projection semantics are stale")
        print("PASS_RESEARCH_GATEWAY_PROJECTION_CURRENT")
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
