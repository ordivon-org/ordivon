from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "architecture" / "structure-r2-transition-r1.json"
MODULE_PATH = ROOT / "tools" / "repo" / "check_structure_r2.py"

spec = importlib.util.spec_from_file_location("check_structure_r2", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def load_plan() -> dict:
    value = json.loads(PLAN.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value

def test_current_structure_r2_plan_is_valid() -> None:
    module.validate_plan(load_plan(), repo_root=ROOT)

def test_semantic_component_type_claim_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["semanticTypeClaim"] = "domain"
    with pytest.raises(module.StructureR2Error, match="semantic component type"):
        module.validate_plan(value)

def test_forbidden_semantic_target_root_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["targetPaths"] = ["services/web/"]
    with pytest.raises(module.StructureR2Error, match="forbidden semantic root"):
        module.validate_plan(value)

def test_unknown_target_root_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["targetPaths"] = ["mystery/web/"]
    with pytest.raises(module.StructureR2Error, match="not admitted"):
        module.validate_plan(value)

@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("targetPaths", "packages/../../services/runtime/"),
        ("targetPaths", "/packages/runtime/"),
        ("sourcePaths", "services/../services/runtime/"),
        ("sourcePaths", "../../services/runtime/"),
        ("targetPaths", "packages//runtime/"),
        ("sourcePaths", "services" + chr(92) + "runtime/"),
    ],
)
def test_mapping_paths_must_be_canonical_repo_relative(field: str, value: str) -> None:
    plan = load_plan()
    plan["mappings"][0][field] = [value]
    with pytest.raises(module.StructureR2Error, match="canonical repository-relative"):
        module.validate_plan(plan)


def test_declared_target_roots_must_be_canonical() -> None:
    plan = load_plan()
    plan["targetRoots"].append("packages/../../services/")
    with pytest.raises(module.StructureR2Error, match="canonical repository-relative"):
        module.validate_plan(plan)


def test_forbidden_roots_must_be_canonical() -> None:
    plan = load_plan()
    plan["forbiddenSemanticRoots"].append("services/../platform/")
    with pytest.raises(module.StructureR2Error, match="canonical repository-relative"):
        module.validate_plan(plan)


def test_missing_current_source_fails_closed() -> None:
    value = load_plan()
    value["mappings"][0]["sourcePaths"] = ["does-not-exist/"]
    with pytest.raises(module.StructureR2Error, match="does not exist"):
        module.validate_plan(value, repo_root=ROOT)

def test_duplicate_mapping_id_fails_closed() -> None:
    value = load_plan()
    value["mappings"].append(copy.deepcopy(value["mappings"][0]))
    with pytest.raises(module.StructureR2Error, match="duplicate mapping id"):
        module.validate_plan(value)

def test_s0_cannot_move_source() -> None:
    value = load_plan()
    s0 = next(w for w in value["waves"] if w["id"] == "S0")
    s0["movesSource"] = True
    with pytest.raises(module.StructureR2Error, match="S0 must not move source"):
        module.validate_plan(value)



def test_partial_deployment_requires_s1a_evidence() -> None:
    value = load_plan()
    value["deployedSlices"] = ["S0", "S1B"]
    with pytest.raises(module.StructureR2Error, match="requires S0 and S1A"):
        module.validate_plan(value)


def test_s1b_cannot_be_deployed_and_open() -> None:
    value = load_plan()
    value["openSlices"].append("S1B")
    with pytest.raises(module.StructureR2Error, match="both deployed and open"):
        module.validate_plan(value)


def test_s1b_must_remain_open_before_deployment() -> None:
    value = load_plan()
    value["deployedSlices"] = [item for item in value["deployedSlices"] if item != "S1B"]
    mapping = next(m for m in value["mappings"] if m["id"] == "composition-mechanics")
    mapping["standing"] = "PARTIALLY_DEPLOYED"
    with pytest.raises(module.StructureR2Error, match="remain explicitly open"):
        module.validate_plan(value)


def test_s1b_deployment_requires_deployed_composition_standing() -> None:
    value = load_plan()
    mapping = next(m for m in value["mappings"] if m["id"] == "composition-mechanics")
    mapping["standing"] = "PARTIALLY_DEPLOYED"
    with pytest.raises(module.StructureR2Error, match="composition standing must be DEPLOYED"):
        module.validate_plan(value)


def test_deployed_move_rejects_retained_source_path() -> None:
    value = load_plan()
    mapping = next(m for m in value["mappings"] if m["id"] == "control-plugin")
    mapping["sourcePaths"] = ["extensions/ordivon-control-plane/"]
    with pytest.raises(module.StructureR2Error, match="deployed move retains source path"):
        module.validate_plan(value, repo_root=ROOT)


def test_deployed_move_rejects_missing_target_path() -> None:
    value = load_plan()
    mapping = next(m for m in value["mappings"] if m["id"] == "control-plugin")
    mapping["targetPaths"] = ["extensions/missing-control-plugin/"]
    with pytest.raises(module.StructureR2Error, match="deployed move target missing"):
        module.validate_plan(value, repo_root=ROOT)


def test_exhaustive_source_cut_has_distinct_semantic_truth_boundary() -> None:
    """Existing Structure R2 CI consumer: source placement != LEGO proof."""
    import subprocess
    spec = importlib.util.spec_from_file_location(
        "ordivon_exhaustive_coverage",
        ROOT / "tools" / "repo" / "exhaustive_coverage.py",
    )
    assert spec is not None and spec.loader is not None
    coverage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(coverage)
    source_cut = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    result = coverage.classification(ROOT, source_cut)
    assert result["summary"]["trackedPaths"] == result["summary"]["accountedForPaths"]
    assert result["summary"]["nodes"] == len(result["semanticPlans"]["nodes"])
    assert result["summary"]["edges"] == len(result["semanticPlans"]["edges"])
    assert result["proofReuseAdmissible"] is False
    assert all(n["formalQualification"] == "UNKNOWN" for n in result["semanticPlans"]["nodes"])
    assert len({p["path"] for p in result["sourcePaths"]}) == result["summary"]["trackedPaths"]


def test_exhaustive_coverage_overlapping_roots_fail_closed() -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ordivon_exhaustive_coverage",
        ROOT / "tools" / "repo" / "exhaustive_coverage.py",
    )
    assert spec is not None and spec.loader is not None
    coverage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(coverage)
    with pytest.raises(ValueError, match="overlapping"):
        coverage.source_partition("services/runtime/main.py", {
            "owners": [
                {"name": "all", "root": "services/"},
                {"name": "runtime", "root": "services/runtime/"},
            ],
        })


def test_phase1_content_scan_exact_source_complete_and_non_authoritative():
    import subprocess
    import importlib.util
    module_path = ROOT / "tools" / "repo" / "source_content_facets.py"
    spec = importlib.util.spec_from_file_location("phase1_source_content", module_path)
    assert spec is not None and spec.loader is not None
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    cut = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    result = scanner.compile_projection(ROOT, cut)
    assert result["summary"]["tracked"] == result["summary"]["accountedFor"]
    assert len(result["paths"]) == len({x["path"] for x in result["paths"]})
    assert result["summary"]["sourcePathMoves"] == 0
    assert result["summary"]["allFunctionalIdentitiesQualified"] == 0
    # Source regions are materialized only when they contain tracked files.
    # Eliminating a genuinely obsolete source-only area must not force an
    # empty synthetic region back into the live source namespace.
    zones = result["summary"]["allZones"]
    assert zones and all(count > 0 for count in zones.values())
    assert sum(zones.values()) == result["summary"]["tracked"]
    assert len([name for name in zones if name.startswith("zone/")]) == 18
    assert len(result["summary"]["dense60"]) == 60
    assert len(result["summary"]["specific26"]) == 26
    assert all(x["mayPhysicallyRename"] is False and x["consumerStanding"]=="UNKNOWN"
               for x in result["summary"]["specific26"])
    assert len(result["summary"]["contentObservedCounterexamples12"]) == 12
    assert all(x["physicalRenameAllowed"] is False
               and x["consumerStanding"]=="UNKNOWN"
               and x["witnessStatus"] in {
                   "WITNESS_NOT_IN_GIT_CUT",
                   "WITNESS_BLOB_CHANGED",
                   "WITNESS_CONTENT_NOT_READ",
                   "WITNESS_GIT_BLOB_AND_LITERAL_MATCH",
                   "WITNESS_MARKER_MISSING"
               }
               for x in result["summary"]["contentObservedCounterexamples12"])
    assert all(x["actualConsumers"] == "UNKNOWN" for x in result["paths"])

def test_phase1_source_form_lexical_names_never_admit_semantic_proof():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "phase1_content_forms",
        ROOT / "tools" / "repo" / "source_content_facets.py",
    )
    assert spec is not None and spec.loader is not None
    forms = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(forms)
    for path, expected in [
        ("docs/migration/receipts/host.commit-map", "HISTORICAL_COMMIT_MAPPING_TEXT"),
        ("services/runtime/formal/RuntimeDispatchR1.tla", "TLA_PLUS_SPECIFICATION_TEXT"),
        ("platform/workstation/n8n/ordivon-n8n.container", "PODMAN_QUADLET_UNIT_TEXT"),
    ]:
        carrier = forms.content_probe(path, "100644", 4, b"text")
        assert carrier["contentForm"] == expected
        assert carrier["readStanding"] == "LEXICAL_SOURCE_FORM_ONLY"
        assert carrier["semanticQualification"] == "UNKNOWN"
    assert forms.MAX_READ_BYTES <= 4 * 1024 * 1024
    stream = forms.content_probe(
        "evidence/runs.jsonl", "100644", 13, b'{"kind":"r1"}\n{"kind":"r2"}'
    )
    assert stream["readStanding"] == "FIRST_RECORD_PARSED_ONLY"
    assert stream["contentForm"] == "JSONL_FIRST_OBJECT_ONLY"
