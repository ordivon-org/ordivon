"""Delegate a real Research decision to the existing producer-owned Data product.

This is a bounded Research consumer, not a new Data platform or study judge.
Data only supplies verified source bytes; Research owns the decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data.catalog import inspect_distribution
from ordivon_data.local_evidence import LocalEvidenceBinding
from ordivon_data.odps_projection import project_odps

PRODUCT = Path("catalogs/data-products/experimental-episode-corpus-r1/odps.json")
ANALYSIS = Path(
    "studies/experimental-episodes/evidence/analysis/experimental-system-analysis-r1.json"
)
RECEIPT = Path(
    "studies/experimental-episodes/evidence/data-products/"
    "experimental-episode-analysis-r1/receipt.json"
)
MANIFEST_PORT = "episode-corpus-manifest-json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_exact_file(root: Path, relative: Path, expected: str) -> dict[str, Any]:
    """Read a consumer source; the stored receipt, not the filename, is authority."""
    root = root.resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("source path escapes approved checkout or is not a file")
    payload = path.read_bytes()
    if digest(payload) != expected:
        raise ValueError(f"source digest mismatch: {relative.as_posix()}")
    result = json.loads(payload)
    if not isinstance(result, dict):
        raise TypeError("consumer source must be a JSON object")
    return result


def deliver(root: Path = ROOT) -> dict[str, Any]:
    """Execute one owner-accepted information delegation, no human tool selection."""
    root = root.resolve(strict=True)
    product_path = root / PRODUCT
    product = json.loads(product_path.read_bytes())
    product_id = product["id"]
    version = product["version"]

    # Exact producer-authorized relative path + digest property mapping.
    # A Research consumer declares ONE needed output, not every catalog port.
    binding = LocalEvidenceBinding(
        product_id=product_id,
        port_name=MANIFEST_PORT,
        path_property="corpusManifestRelativePath",
        digest_property="corpusManifestSha256",
        owner_root=root,
    )
    projected, product_source_digest = project_odps(product_path, bindings=(binding,))
    candidates = [
        port
        for port in projected["dcat:distribution"]
        if port["dct:title"] == MANIFEST_PORT
    ]
    if len(candidates) != 1:
        raise ValueError("required Research output port is absent or ambiguous")
    observed = inspect_distribution(candidates[0], (root,), verify_local=True)
    if observed["verification"] != "VERIFIED":
        raise ValueError("required Research manifest is not verified")

    # Independent consuming reader reopens the same declared source and checks
    # its actual bytes, not merely a previous catalog observation.
    props = {
        item["property"]: item["value"]
        for item in product["customProperties"]
        if isinstance(item, dict) and "property" in item
    }
    source_ref = Path(props["corpusManifestRelativePath"])
    manifest = require_exact_file(root, source_ref, props["corpusManifestSha256"])
    if observed["observedDigest"] != "sha256:" + props["corpusManifestSha256"]:
        raise ValueError("manifest product publication contradicts consumed bytes")

    receipt = json.loads((root / RECEIPT).read_bytes())
    if (
        receipt["productId"] != product_id
        or receipt["productVersion"] != version
        or receipt["corpusManifestSha256"] != props["corpusManifestSha256"]
        or receipt["standing"]
        != "PASS_PRODUCT_TO_SYSTEM_ANALYSIS_WITHOUT_AUTHORITY_TRANSFER"
        or receipt["authorityTransfer"] is not False
    ):
        raise ValueError(
            "Research product-to-analysis receipt is not bound to the source"
        )
    analysis = require_exact_file(root, ANALYSIS, receipt["systemAnalysisSha256"])

    counts = {
        row["profileId"]: row["projectedEpisodes"] for row in manifest["profiles"]
    }
    if len(counts) != len(manifest["profiles"]):
        raise ValueError("duplicate profile identities")
    total = sum(counts.values())
    if total != props["episodeCount"]:
        raise ValueError("Research product count contradicts verified source")
    general = analysis["generalization"]
    intervention = analysis["intervention"]
    if (
        general["developmentEpisodes"] == 0 or general["judgeEpisodes"] == 0
    ) and general["standing"] != "NOT_IDENTIFIED":
        raise ValueError("unsupported positive generalization status")
    if (
        intervention["assignedEpisodes"] == 0
        and intervention["standing"] != "NOT_IDENTIFIED"
    ):
        raise ValueError("unsupported positive intervention status")

    # A product's source facts are not an autonomous Agent skill evaluation.
    return {
        "kind": "ordivon.research.outcome-first-episode-delegation-r1",
        "consumer": "Research / autonomous improvement qualification",
        "requestedOutcome": "Determine if this historical corpus justifies promoting an autonomous learning Agent",
        "status": "ACCEPTED",
        "decision": {
            "standing": "HOLD",
            "reason": (
                "Verified historical input exists, but these records do not "
                "identify task-level generalization or intervention benefit."
            ),
        },
        "observedBusinessFacts": {
            "historicalEpisodeCount": total,
            "profiles": counts,
            "developmentEpisodes": general["developmentEpisodes"],
            "judgeEpisodes": general["judgeEpisodes"],
            "generalizationStanding": general["standing"],
            "interventionStanding": intervention["standing"],
        },
        "deliveredInformation": {
            "productId": product_id,
            "productVersion": version,
            "productSourceDigest": product_source_digest,
            "port": MANIFEST_PORT,
            "manifestSha256": "sha256:" + props["corpusManifestSha256"],
            "systemAnalysisSha256": "sha256:" + receipt["systemAnalysisSha256"],
            "physicalByteVerification": observed["verification"],
            "consumerReadback": "PASS_EXACT_SOURCE_DIGESTS_AND_RESEARCH_RECEIPT",
            "scope": "SELECTED_OUTPUT_PORT_ONLY_NOT_WHOLE_PRODUCT",
        },
        "feedback": {
            "standing": "NO_DATA_CORRECTION_REQUIRED",
            "nextBusinessExperiment": (
                "Use actual producer-owned action/feedback episodes with "
                "separate held-out task outcome verification; do not "
                "interpret this corpus as raw searchable memories."
            ),
        },
        "nonClaims": [
            "No invented Parquet materialization or whole-catalog verification",
            "No financial execution or portfolio recommendation",
            "No Agent task-learning causal uplift identified",
            "No raw Episode replay availability claim",
            "No authorization to delete retained source evidence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = deliver()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        # A failed data handoff is NOT an accepted Research decision.
        report = {
            "kind": "ordivon.research.outcome-first-episode-delegation-r1",
            "status": "DATA_NOT_DELIVERED",
            "decision": {"standing": "NOT_EVALUATED"},
            "reason": f"{type(exc).__name__}: {exc}",
        }
        code = 3
    else:
        code = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "decision": report["decision"]["standing"],
                "receipt": str(args.output),
            }
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
