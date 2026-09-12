from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "openxml_ext", ROOT / "scripts/artifact_openxml_external_evidence.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ArtifactOpenXmlExternalEvidenceTests(unittest.TestCase):
    def test_manifest_preserves_external_provenance_and_non_ivv_boundary(self) -> None:
        manifest = json.loads(
            (ROOT / "artifact-delivery/openxml-external-evidence-r1.json").read_text()
        )
        self.assertEqual(manifest["graduationPolicy"]["ivvStanding"], "NOT_CLAIMED")
        self.assertEqual(manifest["methodId"], "artifact.openxml.conformance.v1")
        self.assertTrue(
            any(
                source["sourceId"] == "openxml-sdk-issue-2128"
                for source in manifest["externalSources"]
            )
        )
        case = next(
            case
            for case in manifest["cases"]
            if case["caseId"] == "EXT-2128-FILTER-THEN-DATE"
        )
        self.assertEqual(
            case["resultAuthority"],
            "LIMITATION_ONLY_DO_NOT_INFER_DOCUMENT_INVALIDITY",
        )

    def test_fixture_generation_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.xlsx"
            second = Path(directory) / "second.xlsx"
            MODULE.make_fixture("xlsx-filter-date", first)
            MODULE.make_fixture("xlsx-filter-date", second)
            self.assertEqual(MODULE.sha(first), MODULE.sha(second))
            self.assertEqual(
                MODULE.sha(first),
                "63292b04f5c15531e22c3400660a6a0390516569ab82d57cb33a1122a416dbed",
            )

    def test_external_evidence_runner_on_production_current(self) -> None:
        if not MODULE.DEFAULT_VALIDATOR.is_file():
            self.skipTest("production OpenXML validator absent")
        result = MODULE.run(MODULE.DEFAULT_VALIDATOR)
        self.assertEqual(result["standing"], "PASS_BOUNDED_EXTERNAL_EVIDENCE")
        self.assertEqual(result["ivvStanding"], "NOT_CLAIMED")
        self.assertEqual(
            result["corpusResultDigest"],
            "sha256:3a0b9739903e4279e25528f3c5a52a4a7d0708ae2803436ffec57b684298b778",
        )
        self.assertEqual(
            result["methodPromotion"], "GRADUATED_BOUNDED_STRUCTURAL_GATE"
        )
        limitation = next(
            case
            for case in result["cases"]
            if case["caseId"] == "EXT-2128-FILTER-THEN-DATE"
        )
        self.assertTrue(limitation["pass"])
        self.assertEqual(limitation["validatorStatus"], "FAIL")
        self.assertEqual(
            limitation["resultAuthority"],
            "LIMITATION_ONLY_DO_NOT_INFER_DOCUMENT_INVALIDITY",
        )


if __name__ == "__main__":
    unittest.main()
