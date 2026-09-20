import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactWebVerifierDecompositionA10Tests(unittest.TestCase):
    def test_web_verifier_package_has_conformance_browser_toolchain_and_runner(self):
        for relative in (
            "artifact_verifiers/web/__init__.py",
            "artifact_verifiers/web/conformance.py",
            "artifact_verifiers/web/browser.py",
            "artifact_verifiers/web/toolchain.py",
            "artifact_verifiers/web/node/verify_html.mjs",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_web_runner_is_no_longer_owned_by_delivery_directory(self):
        self.assertFalse(
            (ROOT / "artifact-delivery/node/verify_html.mjs").exists(),
            "Web verification runner should move with its verifier owner",
        )

    def test_web_verifier_package_does_not_import_delivery_monolith(self):
        for relative in (
            "artifact_verifiers/web/conformance.py",
            "artifact_verifiers/web/browser.py",
            "artifact_verifiers/web/toolchain.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import artifact_delivery", source)
            self.assertNotIn("from artifact_delivery", source)

    def test_package_exports_web_verifier_surface(self):
        from artifact_verifiers.web import (
            verify_html_conformance,
            verify_web_local,
            vnu_jar,
            web_verifier_runner,
        )
        for item in (
            verify_html_conformance,
            verify_web_local,
            vnu_jar,
            web_verifier_runner,
        ):
            self.assertTrue(callable(item))

    def test_verify_stage_wires_directly_to_web_verifier(self):
        source = (
            ROOT / "artifact_operations/providers/direct_python.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "verify_html_conformance=verify_html_conformance",
            source,
        )
        self.assertIn("verify_web_local=verify_web_local", source)


if __name__ == "__main__":
    unittest.main()
