import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactPresentationDecompositionA4Test(unittest.TestCase):
    def test_presentation_capability_package_has_distinct_provider_modules(self):
        expected = [
            ROOT / 'artifact_capabilities/presentation/common.py',
            ROOT / 'artifact_capabilities/presentation/admission.py',
            ROOT / 'artifact_capabilities/presentation/python_pptx.py',
            ROOT / 'artifact_capabilities/presentation/ppt_master.py',
        ]
        for path in expected:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)

    def test_new_package_exports_legacy_compatible_entrypoints(self):
        from artifact_capabilities.presentation import (
            admit_presentation_source,
            admit_semantic_svg_source,
            build_presentation_source,
            build_semantic_svg_presentation_source,
        )
        self.assertTrue(callable(admit_presentation_source))
        self.assertTrue(callable(admit_semantic_svg_source))
        self.assertTrue(callable(build_presentation_source))
        self.assertTrue(callable(build_semantic_svg_presentation_source))

    def test_build_dispatch_still_selects_both_presentation_capabilities(self):
        from artifact_core.build_bindings import BuildCapabilityBindingRegistry
        registry = BuildCapabilityBindingRegistry(ROOT / 'artifact-delivery')
        native = registry.resolve('presentation', 'presentation-source-v1')
        svg = registry.resolve('presentation', 'presentation-semantic-svg-source-v1')
        self.assertEqual(native.adapter_id, 'python-pptx-presentation-source-v1')
        self.assertEqual(svg.adapter_id, 'ppt-master-semantic-svg-v1')


if __name__ == '__main__':
    unittest.main()
