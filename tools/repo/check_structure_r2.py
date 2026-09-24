#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

class StructureR2Error(ValueError):
    pass

REQUIRED_LAWS = {
    "placement-is-not-identity",
    "package-is-source-locality-not-semantic-type",
    "source-topology-is-not-runtime-topology",
    "consumer-depends-on-public-contract-not-provider-internals",
    "default-provider-is-not-capability",
    "extensions-grow-at-edge",
    "skills-do-not-authorize",
    "runtime-state-is-not-source-truth",
    "capability-exposure-is-task-compiled",
    "verification-is-owner-or-seam-specific",
    "natural-authority-remains-external-to-composition",
    "source-relocation-is-separate-from-semantic-refactoring",
}
REQUIRED_ANTI_GROWTH = {
    "universal-capability-registry",
    "root-contract-authority",
    "global-provider-registry",
    "universal-verifier",
}
REQUIRED_LEGACY_ROOTS = {"services/", "platform/", "capabilities/", "domains/", "meta/"}
ALLOWED_MODES = {"retain", "move", "split"}

def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StructureR2Error(f"{field} must be a non-empty string")
    return value.strip()

def _path_root(path: str) -> str:
    normalized = path[2:] if path.startswith("./") else path
    if normalized.startswith(".agents/"):
        return ".agents/"
    return f"{normalized.split('/', 1)[0]}/"

def validate_plan(value: dict[str, Any], *, repo_root: Path | None = None) -> None:
    if value.get("schemaVersion") != 1:
        raise StructureR2Error("schemaVersion must be 1")
    if value.get("kind") != "ordivon.repository-structure-transition":
        raise StructureR2Error("unexpected plan kind")
    status = value.get("status")
    if status not in {"candidate-not-deployed", "partially-deployed"}:
        raise StructureR2Error("unexpected Structure R2 deployment status")
    if status == "partially-deployed":
        deployed = value.get("deployedSlices")
        open_slices = value.get("openSlices")
        if not isinstance(deployed, list) or not {"S0", "S1A"}.issubset(set(deployed)):
            raise StructureR2Error("partially-deployed status requires S0 and S1A evidence")
        if not isinstance(open_slices, list):
            raise StructureR2Error("partially-deployed status requires openSlices")
        s1b_deployed = "S1B" in deployed
        if s1b_deployed and "S1B" in open_slices:
            raise StructureR2Error("S1B cannot be both deployed and open")
        if not s1b_deployed and "S1B" not in open_slices:
            raise StructureR2Error("S1B must remain explicitly open until consumer cutover closes")
    if value.get("truthRole") != "repository-placement-plan-not-runtime-or-domain-authority":
        raise StructureR2Error("unexpected truthRole")

    target_roots = value.get("targetRoots")
    if not isinstance(target_roots, list) or not target_roots:
        raise StructureR2Error("targetRoots must be a non-empty list")
    target_roots_set = {_text(x, field="targetRoots entry") for x in target_roots}
    if len(target_roots_set) != len(target_roots):
        raise StructureR2Error("targetRoots must be unique")

    forbidden = value.get("forbiddenSemanticRoots")
    if not isinstance(forbidden, list) or not forbidden:
        raise StructureR2Error("forbiddenSemanticRoots must be a non-empty list")
    forbidden_set = {_text(x, field="forbiddenSemanticRoots entry") for x in forbidden}
    if REQUIRED_LEGACY_ROOTS - forbidden_set:
        raise StructureR2Error("legacy semantic roots must remain forbidden target roots")
    if target_roots_set & forbidden_set:
        raise StructureR2Error("targetRoots and forbiddenSemanticRoots must not overlap")

    laws = value.get("laws")
    if not isinstance(laws, list) or REQUIRED_LAWS - set(laws):
        raise StructureR2Error("required Structure R2 laws are missing")
    anti_growth = value.get("antiGrowth")
    if not isinstance(anti_growth, list) or REQUIRED_ANTI_GROWTH - set(anti_growth):
        raise StructureR2Error("required anti-growth rules are missing")

    waves = value.get("waves")
    if not isinstance(waves, list) or not waves:
        raise StructureR2Error("waves must be a non-empty list")
    wave_ids: set[str] = set()
    for wave in waves:
        if not isinstance(wave, dict):
            raise StructureR2Error("every wave must be an object")
        wave_id = _text(wave.get("id"), field="wave.id")
        if wave_id in wave_ids:
            raise StructureR2Error(f"duplicate wave id: {wave_id}")
        wave_ids.add(wave_id)
        _text(wave.get("purpose"), field=f"{wave_id}.purpose")
        if not isinstance(wave.get("movesSource"), bool):
            raise StructureR2Error(f"{wave_id}.movesSource must be boolean")
    if "S0" not in wave_ids:
        raise StructureR2Error("S0 wave is required")
    if next(w for w in waves if w["id"] == "S0")["movesSource"]:
        raise StructureR2Error("S0 must not move source")

    mappings = value.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        raise StructureR2Error("mappings must be a non-empty list")
    ids: set[str] = set()
    covered_legacy_roots: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise StructureR2Error("every mapping must be an object")
        mapping_id = _text(mapping.get("id"), field="mapping.id")
        if mapping_id in ids:
            raise StructureR2Error(f"duplicate mapping id: {mapping_id}")
        ids.add(mapping_id)

        mode = _text(mapping.get("mode"), field=f"{mapping_id}.mode")
        if mode not in ALLOWED_MODES:
            raise StructureR2Error(f"{mapping_id}: unsupported mode {mode}")
        wave = _text(mapping.get("wave"), field=f"{mapping_id}.wave")
        if wave not in wave_ids:
            raise StructureR2Error(f"{mapping_id}: unknown wave {wave}")
        _text(mapping.get("owner"), field=f"{mapping_id}.owner")
        if mapping.get("semanticTypeClaim") != "none":
            raise StructureR2Error(
                f"{mapping_id}: directory mapping must not claim a semantic component type"
            )

        source_paths = mapping.get("sourcePaths")
        historical_source_paths = mapping.get("historicalSourcePaths", [])
        target_paths = mapping.get("targetPaths")
        verify_tasks = mapping.get("verifyTasks")
        if not isinstance(source_paths, list):
            raise StructureR2Error(f"{mapping_id}: sourcePaths must be a list")
        if not isinstance(historical_source_paths, list):
            raise StructureR2Error(f"{mapping_id}: historicalSourcePaths must be a list")
        deployed = mapping.get("standing") == "DEPLOYED"
        if not source_paths and not (deployed and historical_source_paths):
            raise StructureR2Error(
                f"{mapping_id}: sourcePaths may be empty only for a deployed mapping with historicalSourcePaths"
            )
        if historical_source_paths and not deployed:
            raise StructureR2Error(
                f"{mapping_id}: historicalSourcePaths require DEPLOYED standing"
            )
        if not isinstance(target_paths, list) or not target_paths:
            raise StructureR2Error(f"{mapping_id}: targetPaths must be non-empty")
        if not isinstance(verify_tasks, list) or not verify_tasks:
            raise StructureR2Error(f"{mapping_id}: verifyTasks must be non-empty")

        for source in source_paths:
            source = _text(source, field=f"{mapping_id}.sourcePath")
            source_root = _path_root(source)
            if source_root in REQUIRED_LEGACY_ROOTS:
                covered_legacy_roots.add(source_root)
            if repo_root is not None and not (repo_root / source.rstrip("/")).exists():
                deployed_move = mode == "move" and mapping.get("standing") == "DEPLOYED"
                if not deployed_move:
                    raise StructureR2Error(
                        f"{mapping_id}: current source path does not exist: {source}"
                    )

        for source in historical_source_paths:
            source = _text(source, field=f"{mapping_id}.historicalSourcePath")
            source_root = _path_root(source)
            if source_root in REQUIRED_LEGACY_ROOTS:
                covered_legacy_roots.add(source_root)
            if repo_root is not None and (repo_root / source.rstrip("/")).exists():
                raise StructureR2Error(
                    f"{mapping_id}: historical source path still exists: {source}"
                )

        for target in target_paths:
            target = _text(target, field=f"{mapping_id}.targetPath")
            target_root = _path_root(target)
            if target_root in forbidden_set:
                raise StructureR2Error(
                    f"{mapping_id}: target re-encodes forbidden semantic root {target_root}"
                )
            if target_root not in target_roots_set:
                raise StructureR2Error(
                    f"{mapping_id}: target root is not admitted by Structure R2: {target_root}"
                )

        for task in verify_tasks:
            _text(task, field=f"{mapping_id}.verifyTask")

    if repo_root is not None:
        for mapping in mappings:
            if mapping.get("standing") != "DEPLOYED":
                continue
            if mapping.get("mode") == "move":
                for source in mapping.get("sourcePaths", []):
                    if (repo_root / source).exists():
                        raise StructureR2Error(
                            f"{mapping.get('id')}: deployed move retains source path: {source}"
                        )
            if mapping.get("mode") in {"move", "split"}:
                for target in mapping.get("targetPaths", []):
                    if not (repo_root / target).exists():
                        raise StructureR2Error(
                            f"{mapping.get('id')}: deployed {mapping.get('mode')} target missing: {target}"
                        )

    if status == "partially-deployed":
        composition = next((m for m in mappings if m.get("id") == "composition-mechanics"), None)
        if composition is None or composition.get("wave") != "S1A":
            raise StructureR2Error("partial deployment requires composition-mechanics in S1A")
        deployed = set(value.get("deployedSlices") or [])
        s1b_deployed = "S1B" in deployed
        expected_standing = "DEPLOYED" if s1b_deployed else "PARTIALLY_DEPLOYED"
        if composition.get("standing") != expected_standing:
            raise StructureR2Error(f"composition standing must be {expected_standing}")
        if repo_root is not None:
            if not (repo_root / "packages/composition").is_dir():
                raise StructureR2Error("S1A claims deployment but packages/composition is absent")
            facades = [
                repo_root / "meta/next/scripts/cognitive_circuit_r1.py",
                repo_root / "meta/next/scripts/interface_contract_r2.py",
            ]
            facade_presence = [path.is_file() for path in facades]
            if s1b_deployed and any(facade_presence):
                raise StructureR2Error("S1B deployed state requires historical facades to be absent")
            if not s1b_deployed and not all(facade_presence):
                raise StructureR2Error("S1B open state requires both historical facades")

    missing_legacy = REQUIRED_LEGACY_ROOTS - covered_legacy_roots
    if missing_legacy:
        raise StructureR2Error(
            f"legacy semantic roots lack explicit transition coverage: {sorted(missing_legacy)}"
        )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", nargs="?", default="docs/architecture/structure-r2-transition-r1.json")
    parser.add_argument("--skip-source-existence", action="store_true")
    args = parser.parse_args()
    path = Path(args.plan)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise StructureR2Error("plan root must be an object")
        repo_root = None if args.skip_source_existence else Path(".")
        validate_plan(value, repo_root=repo_root)
    except (OSError, json.JSONDecodeError, StructureR2Error) as exc:
        print(f"structure r2 check failed: {exc}")
        return 2
    print(f"structure r2 check passed: {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
