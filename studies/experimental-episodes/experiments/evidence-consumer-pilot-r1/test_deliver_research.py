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

    def test_source_bytes_tampered_rejected(self) -> None:
        self.manifest.write_bytes(self.manifest.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "digest"):
            delivery.deliver(self.root)

    def test_source_manifest_missing_rejected(self) -> None:
        self.manifest.unlink()
        with self.assertRaises(OSError):
            delivery.deliver(self.root)

    def test_analysis_drift_rejected_against_research_receipt(self) -> None:
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
