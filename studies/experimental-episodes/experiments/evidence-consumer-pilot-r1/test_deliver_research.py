"""Real source-backed and negative producer-to-Research delegation qualification."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "research_outcome_delivery", HERE / "deliver_research.py"
)
assert spec and spec.loader
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class ResearchOutcomeDelegationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ordivon-research-data-handoff-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in (delivery.PRODUCT, delivery.ANALYSIS, delivery.RECEIPT):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(delivery.ROOT / relative, target)
        product = json.loads((self.root / delivery.PRODUCT).read_text())
        props = {p["property"]: p["value"] for p in product["customProperties"]}
        self.manifest = self.root / props["corpusManifestRelativePath"]
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            delivery.ROOT / props["corpusManifestRelativePath"], self.manifest
        )

    def test_business_handoff_returns_research_decision_not_tool_steps(self) -> None:
        result = delivery.deliver(self.root)
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(result["decision"]["standing"], "HOLD")
        self.assertEqual(
            result["observedBusinessFacts"]["historicalEpisodeCount"], 10007
        )
        self.assertEqual(
            result["deliveredInformation"]["physicalByteVerification"], "VERIFIED"
        )
        self.assertEqual(
            result["deliveredInformation"]["scope"],
            "SELECTED_OUTPUT_PORT_ONLY_NOT_WHOLE_PRODUCT",
        )
        self.assertEqual(result["feedback"]["standing"], "NO_DATA_CORRECTION_REQUIRED")

    def test_irrelevant_unavailable_parquet_does_not_block_selected_json(self) -> None:
        self.assertFalse((self.root / "episode-index.parquet").exists())
        self.assertEqual(delivery.deliver(self.root)["status"], "ACCEPTED")

    def test_manifest_port_contract_version_drift_is_not_accepted(self) -> None:
        product_path = self.root / delivery.PRODUCT
        product = json.loads(product_path.read_text())
        manifest_port = next(
            x for x in product["outputPorts"] if x["name"] == delivery.MANIFEST_PORT
        )
        self.assertEqual(manifest_port["version"], "1.0.0")
        manifest_port["version"] = "2.0.0"
        product_path.write_text(json.dumps(product))
        with self.assertRaisesRegex(ValueError, "version"):
            delivery.deliver(self.root)

    def test_same_named_unrelated_v2_does_not_block_required_v1(self) -> None:
        product_path = self.root / delivery.PRODUCT
        product = json.loads(product_path.read_text())
        manifest_port = next(
            x for x in product["outputPorts"] if x["name"] == delivery.MANIFEST_PORT
        )
        self.assertEqual(manifest_port["version"], "1.0.0")
        unrelated_v2 = dict(manifest_port)
        unrelated_v2["version"] = "2.0.0"
        unrelated_v2.pop("id", None)  # ODPS 1.1 ID is optional
        product["outputPorts"].append(unrelated_v2)
        product_path.write_text(json.dumps(product))
        self.assertEqual(delivery.deliver(self.root)["status"], "ACCEPTED")

    def test_source_bytes_tampered_rejected(self) -> None:
        self.manifest.write_bytes(self.manifest.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "digest"):
            delivery.deliver(self.root)

    def test_source_manifest_missing_rejected(self) -> None:
        self.manifest.unlink()
        with self.assertRaises(OSError):
            delivery.deliver(self.root)

    def test_analysis_drift_rejected_against_research_receipt(self) -> None:
        # Data verifies the selected producer port, but cannot confer
        # Research's independent business acceptance.
        product = json.loads((self.root / delivery.PRODUCT).read_text())
        binding = delivery.LocalEvidenceBinding(
            product_id=product["id"],
            port_name=delivery.MANIFEST_PORT,
            path_property="corpusManifestRelativePath",
            digest_property="corpusManifestSha256",
            owner_root=self.root,
            port_version=delivery.MANIFEST_PORT_VERSION,
        )
        projected, _ = delivery.project_odps(
            self.root / delivery.PRODUCT, bindings=(binding,)
        )
        selected = next(
            p
            for p in projected["dcat:distribution"]
            if p["dct:title"] == delivery.MANIFEST_PORT
            and p.get("dcat:version") == delivery.MANIFEST_PORT_VERSION
        )
        self.assertEqual(
            delivery.inspect_distribution(selected, (self.root,), verify_local=True)[
                "verification"
            ],
            "VERIFIED",
        )
        f = self.root / delivery.ANALYSIS
        d = json.loads(f.read_text())
        d["generalization"]["developmentEpisodes"] = 999
        f.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "source digest mismatch"):
            delivery.deliver(self.root)

    def test_research_receipt_product_identity_mismatch_rejected(self) -> None:
        f = self.root / delivery.RECEIPT
        d = json.loads(f.read_text())
        d["productId"] = "wrong-producer"
        f.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "receipt"):
            delivery.deliver(self.root)

    def test_source_path_traversal_rejected_by_existing_data_owner(self) -> None:
        f = self.root / delivery.PRODUCT
        d = json.loads(f.read_text())
        for item in d["customProperties"]:
            if item["property"] == "corpusManifestRelativePath":
                item["value"] = "../../outside/secret.json"
        f.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, "escape"):
            delivery.deliver(self.root)

    def test_unsupported_promotion_signal_rejected_even_if_receipt_forged(self) -> None:
        analysis_path = self.root / delivery.ANALYSIS
        a = json.loads(analysis_path.read_text())
        a["generalization"]["standing"] = "GENERALIZED"
        analysis_path.write_text(json.dumps(a))
        receipt_path = self.root / delivery.RECEIPT
        receipt = json.loads(receipt_path.read_text())
        receipt["systemAnalysisSha256"] = delivery.digest(analysis_path.read_bytes())
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "unsupported positive"):
            delivery.deliver(self.root)

    def test_original_checkout_consumer_decision_matches_frozen_receipt(self) -> None:
        result = delivery.deliver()
        self.assertEqual(result["decision"]["standing"], "HOLD")
        self.assertEqual(result["observedBusinessFacts"]["judgeEpisodes"], 0)
        self.assertEqual(result["observedBusinessFacts"]["developmentEpisodes"], 0)


if __name__ == "__main__":
    unittest.main()
