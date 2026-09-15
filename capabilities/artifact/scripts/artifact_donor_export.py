#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifact-delivery"
V2 = ART / "shadow-v2/examples"
TAXONOMY = ART / "taxonomy-v1.json"
SCHEMA = ART / "donor-r1/donor-manifest.schema.json"

VALIDATOR_BY_PROFILE = {
    "dataset-parquet-flat-r1": "scripts/artifact_dataset.py",
    "still-image-png-srgb-r1": "scripts/artifact_still_image.py",
    "still-image-svg-static-r1": "scripts/artifact_svg.py",
    "audio-flac-pcm16-r1": "scripts/artifact_audio.py",
    "audio-wave-pcm16-r1": "scripts/artifact_wave.py",
    "audio-ogg-vorbis-r1": "scripts/artifact_ogg_vorbis.py",
    "moving-image-matroska-ffv1-v3-r1": "scripts/artifact_moving_image.py",
    "geospatial-geopackage-point-r1": "scripts/artifact_geospatial.py",
    "design-2d-tiled-tmj-object-map-r1": "scripts/artifact_tiled.py",
    "design-2d-aseprite-horizontal-sheet-r1": "scripts/artifact_aseprite.py",
    "design-3d-glb-static-mesh-r1": "scripts/artifact_design3d.py",
    "design-3d-glb-material-scene-r1": "scripts/artifact_design3d.py",
    "design-3d-glb-skinned-animation-r1": "scripts/artifact_design3d.py",
    "software-release-oci-image-r1": "scripts/artifact_software_release.py",
    "software-release-linux-elf-executable-r1": "scripts/artifact_software_release_elf.py",
    "web-archive-warc-response-r1": "scripts/artifact_web_archive.py",
    "message-internet-text-r1": "scripts/artifact_message.py",
    "eda-kicad-pcb-gerber-r1": "scripts/artifact_eda.py",
    "eda-spice-transient-measure-r1": "scripts/artifact_spice.py",
    "design-3d-step-solid-r1": "scripts/artifact_cad_step.py",
}

EXCLUDED = [
    ("legacy Artifact delivery orchestration", "scripts/artifact_delivery.py", "Mixed production orchestration and historical compatibility are execution implementation, not reusable problem knowledge."),
    ("Temporal Artifact execution wiring", "scripts/artifact_delivery_temporal_support.py", "Durability and activity execution belong to the replaceable workflow provider layer."),
    ("Artifact OCI package/release adapter", "scripts/artifact_oci_package.py", "OCI packaging is release infrastructure and a replaceable capability provider, not Artifact problem ontology."),
    ("R2 mailbox transport implementation", "scripts/artifact_r2_mailbox.py", "Transport/effect reconciliation belongs to delivery infrastructure rather than Artifact classification or validation knowledge."),
    ("toolchain doctor", "scripts/artifact_delivery_toolchain_doctor.py", "Environment probing is provider integration and should remain replaceable."),
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(relative: str) -> dict[str, str]:
    p = ROOT / relative
    if not p.is_file():
        raise FileNotFoundError(relative)
    return {"path": relative, "sha256": sha(p)}

def load(path: Path) -> Any:
    return json.loads(path.read_text())

def family_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {x["id"]: x for x in taxonomy["families"]}

def bindings_by_profile() -> dict[str, tuple[Path, dict[str, Any]]]:
    out = {}
    for p in sorted((ART / "shadow-bindings").glob("*.json")):
        x = load(p)
        out[x["profileId"]] = (p, x)
    return out

def build(base_revision: str) -> dict[str, Any]:
    taxonomy = load(TAXONOMY)
    families = family_index(taxonomy)
    bindings = bindings_by_profile()
    profiles = []
    represented = set()
    live_bindings = 0
    isolated_validators = 0

    for p in sorted(V2.glob("*-v2.json")):
        x = load(p)
        pid = x["id"]
        family = x["classification"]["family"]
        represented.add(family)
        if family not in families:
            raise ValueError(f"profile {pid} references unknown family {family}")

        binding_obj = None
        capability_signals = [a.get("name", "") for a in x.get("targetAuthorities", []) if a.get("name")]
        if pid in bindings:
            bp, bx = bindings[pid]
            if bx.get("status") == "LOCAL_LIVE_PROVEN":
                live_bindings += 1
            binding_keys = sorted((bx.get("bindings") or {}).keys())
            capability_signals.extend(binding_keys)
            binding_obj = {
                "standing": bx.get("status", "UNKNOWN"),
                "bindingKeys": binding_keys,
                "proofKeys": sorted((bx.get("proof") or {}).keys()),
                "reference": ref(str(bp.relative_to(ROOT))),
            }

        validator_obj = None
        vp = VALIDATOR_BY_PROFILE.get(pid)
        if vp:
            validator_obj = ref(vp)
            isolated_validators += 1

        contract_obj = None
        if x.get("objectContract"):
            declaration = x["objectContract"]
            schema_ref = declaration.get("schemaReference")
            if schema_ref:
                contract_obj = {
                    "declaration": declaration,
                    "schema": ref(str((ART / schema_ref).relative_to(ROOT))),
                }
            elif declaration.get("required"):
                raise ValueError(f"required contract lacks schemaReference: {pid}")

        required_evidence = x["requiredEvidence"]
        profiles.append({
            "profileId": pid,
            "candidateProblemKey": f"artifact/{family}/{pid}",
            "classification": x["classification"],
            "sourceProfile": ref(str(p.relative_to(ROOT))),
            "standards": families[family].get("standards", []),
            "targetAuthorities": x.get("targetAuthorities", []),
            "objectContract": contract_obj,
            "capabilityBinding": binding_obj,
            "validatorImplementation": validator_obj,
            "validationMapping": required_evidence,
            "compositionCandidate": {
                "status": "DECLARATIVE_PROFILE_CANDIDATE",
                "capabilitySignals": sorted(set(capability_signals)),
                "requiredEvidence": sorted(k for k, v in required_evidence.items() if v.get("required")),
                "sequencing": "NOT_ENCODED_DO_NOT_INFER",
            },
            "resultBoundary": {"nonClaims": x.get("nonClaims", [])},
            "migrationDisposition": {
                "classification": "DIRECT_REFERENCE",
                "standards": "DIRECT_REFERENCE",
                "objectContract": "SEMANTIC_MAPPING",
                "capabilityBinding": "SEMANTIC_MAPPING",
                "validationMapping": "SEMANTIC_MAPPING",
                "evidenceRequirements": "DIRECT_REFERENCE",
                "resultBoundary": "DIRECT_REFERENCE",
                "executionWiring": "DO_NOT_PROMOTE",
            },
        })

    excluded = []
    for concept, path, reason in EXCLUDED:
        excluded.append({
            "concept": concept,
            "reference": ref(path) if (ROOT / path).is_file() else None,
            "disposition": "DO_NOT_PROMOTE",
            "reason": reason,
        })

    return {
        "schemaVersion": 1,
        "kind": "artifact-knowledge-to-action-donor",
        "id": "artifact-k2a-donor-r1",
        "standing": "DONOR_REFERENCE_NOT_CORE_ONTOLOGY",
        "baseRevision": base_revision,
        "sourceReferences": {
            "taxonomy": ref("artifact-delivery/taxonomy-v1.json"),
            "profileV2MappingManifest": ref("artifact-delivery/shadow-v2/profile-v2-mapping-manifest-r1.json"),
        },
        "principles": [
            "reference proven Artifact assets instead of copying or re-owning them",
            "preserve external standards and tool identities as knowledge/capability references",
            "do not infer workflow sequence when the source profile did not encode sequence",
            "do not promote Temporal, Runtime, transport or legacy delivery wiring into Ordivon Core",
            "candidateProblemKey is a donor lookup key, not a universal Core ontology commitment",
            "profile PASS boundaries and nonClaims migrate with the validation knowledge",
        ],
        "migrationClasses": {
            "DIRECT_REFERENCE": "Keep the source semantics and provenance as-is; only relocate/index later.",
            "SEMANTIC_MAPPING": "Map the source concept into future Common Contracts without assuming the current Artifact schema is universal.",
            "DO_NOT_PROMOTE": "Keep only as a replaceable execution/provider adapter or historical implementation; never treat it as Core ontology.",
        },
        "coverage": {
            "taxonomyFamilies": len(families),
            "representedFamilies": len(represented),
            "normalizedProfiles": len(profiles),
            "liveProvenShadowBindings": live_bindings,
            "isolatedValidatorImplementations": isolated_validators,
        },
        "knownGaps": [
            {
                "id": "object-contract-coverage",
                "standing": "PRESERVE_GAP_DO_NOT_INVENT",
                "observation": {
                    "profilesWithExplicitObjectContract": sum(p["objectContract"] is not None for p in profiles),
                    "profilesWithoutExplicitObjectContract": sum(p["objectContract"] is None for p in profiles),
                },
            },
            {
                "id": "result-boundary-coverage",
                "standing": "PRESERVE_GAP_DO_NOT_INVENT",
                "observation": {
                    "profilesWithExplicitNonClaims": sum(bool(p["resultBoundary"]["nonClaims"]) for p in profiles),
                    "profilesWithoutExplicitNonClaims": sum(not bool(p["resultBoundary"]["nonClaims"]) for p in profiles),
                },
            },
            {
                "id": "composition-sequencing",
                "standing": "PRESERVE_GAP_DO_NOT_INVENT",
                "observation": {
                    "profilesWithEncodedSequence": 0,
                    "profilesWithoutEncodedSequence": len(profiles),
                },
            },
        ],
        "profiles": profiles,
        "excludedInfrastructure": excluded,
    }

def validate(x: dict[str, Any]) -> list[str]:
    schema = load(SCHEMA)
    v = jsonschema.Draft202012Validator(schema)
    return [e.message for e in sorted(v.iter_errors(x), key=lambda e: list(e.path))]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-revision", required=True)
    ap.add_argument("--output", type=Path, default=ART / "donor-r1/manifest.json")
    args = ap.parse_args()
    if len(args.base_revision) != 40 or any(c not in "0123456789abcdef" for c in args.base_revision):
        raise SystemExit("--base-revision must be a lowercase 40-hex Git revision")
    out = build(args.base_revision)
    failures = validate(out)
    if failures:
        raise SystemExit("donor manifest schema failures: " + "; ".join(failures))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(out["coverage"], sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
