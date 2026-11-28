from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_DIR = ROOT / "data-products/crypto-public-shadow-r2"
SOURCE = ROOT / "evidence/crypto-public-shadow-r2-20260914.json"
SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"

# Frozen consumer obligation, independent of the producer's list order or
# editable acceptance metadata. This consumer does not select a new product.
PRODUCT_ID = "d14d7457-c9aa-59e0-8bf5-7783cea39c1c"
PRODUCT_VERSION = "2026.09.14"
PORT_ID = "358e57ff-d416-5dd6-a90c-f62b4bc94ff0"
PORT_NAME = "public-shadow-json"
PORT_TYPE = "file/json"
CONTRACT_ID = "5de34add-dca7-54eb-ada3-5e657a7c3ff3"


def select_frozen_output_port(product: dict, acceptance: dict) -> dict:
    """Select one exact consumer-qualified port; no positional fallback.

    Equivalent UUID spellings count toward ambiguity but are not admitted
    in place of the frozen canonical identity. Unrelated ports may be
    reordered without changing the selected subject.
    """
    ports = product.get("outputPorts")
    if not isinstance(ports, list) or not all(
        isinstance(port, dict) and isinstance(port.get("id"), str) for port in ports
    ):
        raise ValueError("public shadow product acceptance failed: output port shape")
    candidates = []
    for port in ports:
        try:
            equivalent = str(uuid.UUID(port["id"])) == PORT_ID
        except ValueError:
            equivalent = False
        if equivalent:
            candidates.append(port)
    if len(candidates) != 1:
        raise ValueError("public shadow product acceptance failed: unique output port")
    port = candidates[0]
    expected = {
        "id": PORT_ID, "name": PORT_NAME, "type": PORT_TYPE,
        "version": PRODUCT_VERSION, "contractId": CONTRACT_ID,
    }
    if any(port.get(key) != value for key, value in expected.items()) or (
        acceptance.get("contractId") != CONTRACT_ID
    ):
        raise ValueError("public shadow product acceptance failed: exact output port contract")
    return port


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=ROOT / "evidence/data-products/crypto-public-shadow-consumption-r1")
    args = ap.parse_args()

    product = json.loads((PRODUCT_DIR / "odps.json").read_text())
    acceptance = json.loads((PRODUCT_DIR / "acceptance.json").read_text())
    governance = json.loads((PRODUCT_DIR / "governance-policy.odrl.jsonld").read_text())
    source = json.loads(SOURCE.read_text())
    source_sha = sha(SOURCE)

    stream = source["streaming"]
    # A frozen consumer contract is executable under both python and python -O.
    # Do not use assert: optimized interpreters remove these acceptance gates.
    requirements = (
        ("source digest", source_sha == acceptance["sourceSha256"]),
        ("product identity", product["id"] == acceptance["productId"] == PRODUCT_ID),
        ("product version", product["version"] == PRODUCT_VERSION),
        ("public-only credentials", source["brokerCredentialsUsed"] is False),
        ("no private account data", source["privateAccountDataUsed"] is False),
        ("no external financial writes", source["externalFinancialWritesAttempted"] is False),
        ("accepted snapshot count", stream["acceptedSnapshotCount"] == 4),
        ("measured window count", len(stream["measured"]) == 3),
        ("qualified measured windows", all(m["qualified"] is True for m in stream["measured"])),
        ("source span bound", all(m["sourceTimeSpanLimitMs"] == 1200 for m in stream["measured"])),
        ("receive span bound", all(m["receiveTimeSpanLimitMs"] == 1200 for m in stream["measured"])),
        ("rights prohibitions", {x["action"] for x in governance["prohibition"]} == {"distribute", "grantUse", "delete"}),
    )
    for label, valid in requirements:
        if not valid:
            raise ValueError(f"public shadow product acceptance failed: {label}")

    port = select_frozen_output_port(product, acceptance)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    decision = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.data-product-consumption-decision",
        "product": {
            "id": product["id"],
            "version": product["version"],
            "outputPortId": port["id"],
            "sourceSha256": source_sha,
        },
        "claim": {
            "standing": "FIT_FOR_BOUNDED_PUBLIC_MARKET_MONITORING",
            "basis": {
                "acceptedSnapshotCount": 4,
                "measuredWindowCount": 3,
                "allMeasuredQualified": True,
                "venues": ["BINANCE", "OKX"],
                "assets": ["BTC", "ETH"],
            },
        },
        "decision": {
            "standing": "NO_EXECUTION_OR_DIRECTIONAL_ACTION_ADMITTED",
            "reason": "The product proves bounded public observation only and explicitly excludes execution authority, alpha, arbitrage and price-direction claims.",
        },
        "action": {
            "standing": "NO_EXTERNAL_EFFECT",
            "externalFinancialWriteAttempted": False,
            "privateEndpointAccessAttempted": False,
        },
        "outcome": {
            "standing": "PASS_BOUNDARY_PRESERVED",
            "externalFinancialWriteObserved": False,
            "privateAccountDataConsumed": False,
        },
        "feedback": {
            "collectionPolicyDisposition": "KEEP_CURRENT_PUBLIC_OBSERVATION_BOUNDARY",
            "qualityGateDisposition": "KEEP_FROZEN_1200MS_SOURCE_AND_RECEIVE_SPAN_GATES",
            "modelPolicyDisposition": "NO_DIRECTIONAL_MODEL_UPDATE_FROM_THIS_PRODUCT",
            "governanceDisposition": "KEEP_FAIL_CLOSED_RIGHTS_AND_RETENTION_POLICY",
            "changeRequired": False,
            "reason": "All three measured windows satisfy the frozen coherence gates and the product contains no evidence that justifies expanding execution, rights, privacy, or directional-model claims.",
        },
    }
    decision_path = out / "decision-outcome-feedback.json"
    decision_path.write_text(json.dumps(decision, indent=2) + "\n")
    decision_sha = sha(decision_path)

    run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{product['id']}:{product['version']}:{decision_sha}"))
    input_name = f"{product['id']}@{product['version']}#{port['id']}@sha256:{source_sha}"
    output_name = f"decision-outcome-feedback.json@sha256:{decision_sha}"
    events = [
        {
            "eventTime": now(),
            "eventType": "START",
            "inputs": [{"namespace": "urn:ordivon:data-product:finance", "name": input_name}],
            "job": {"namespace": "urn:ordivon:capital:market-observation", "name": "crypto-public-shadow-product-consumption-r1"},
            "outputs": [],
            "producer": "urn:ordivon:capital:data-product-consumption-r1",
            "run": {"runId": run_id},
            "schemaURL": SCHEMA_URL,
        },
        {
            "eventTime": now(),
            "eventType": "COMPLETE",
            "inputs": [{"namespace": "urn:ordivon:data-product:finance", "name": input_name}],
            "job": {"namespace": "urn:ordivon:capital:market-observation", "name": "crypto-public-shadow-product-consumption-r1"},
            "outputs": [{"namespace": "urn:ordivon:capital:decision-support", "name": output_name}],
            "producer": "urn:ordivon:capital:data-product-consumption-r1",
            "run": {"runId": run_id},
            "schemaURL": SCHEMA_URL,
        },
    ]
    (out / "openlineage.json").write_text(json.dumps(events, indent=2) + "\n")
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.data-product-consumption",
        "standing": "PASS_PRODUCT_TO_DECISION_OUTCOME_FEEDBACK_NO_EXTERNAL_EFFECT",
        "productId": product["id"],
        "productVersion": product["version"],
        "outputPortId": port["id"],
        "sourceSha256": source_sha,
        "decisionArtifactSha256": decision_sha,
        "openLineageRunId": run_id,
        "externalFinancialWriteAttempted": False,
        "feedbackChangeRequired": False,
        "feedbackDisposition": decision["feedback"],
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
