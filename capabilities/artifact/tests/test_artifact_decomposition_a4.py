import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / 'scripts/artifact_delivery.py'


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

    def test_delivery_no_longer_owns_presentation_provider_mechanics(self):
        source = DELIVERY.read_text(encoding='utf-8')
        tree = ast.parse(source)
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in {
            '_resolve_semantic_svg_source_path',
            '_semantic_svg_source_material_facts',
            '_ppt_master_provider_facts',
            '_resolve_presentation_template',
            '_resolve_presentation_image',
            '_presentation_source_material_facts',
            '_presentation_template_package_fact',
            '_presentation_layout_by_id',
            '_presentation_layout_fact',
            '_apply_text_to_shape',
        }:
            self.assertNotIn(name, definitions)
        self.assertNotIn('TemporaryDirectory(prefix="ordivon-artifact-ppt-master-parent-")', source)
        self.assertNotIn('from pptx import Presentation', source)

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

    def test_delivery_public_builders_are_thin_compatibility_wrappers(self):
        spec = importlib.util.spec_from_file_location('artifact_delivery_a4', DELIVERY)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertTrue(callable(module.build_presentation_source))
        self.assertTrue(callable(module.build_semantic_svg_presentation_source))
        source = DELIVERY.read_text(encoding='utf-8')
        tree = ast.parse(source)
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertLessEqual(funcs['build_presentation_source'].end_lineno - funcs['build_presentation_source'].lineno + 1, 18)
        self.assertLessEqual(funcs['build_semantic_svg_presentation_source'].end_lineno - funcs['build_semantic_svg_presentation_source'].lineno + 1, 18)

    def test_build_dispatch_still_selects_both_presentation_capabilities(self):
        from artifact_core.build_bindings import BuildCapabilityBindingRegistry
        registry = BuildCapabilityBindingRegistry(ROOT / 'artifact-delivery')
        native = registry.resolve('presentation', 'presentation-source-v1')
        svg = registry.resolve('presentation', 'presentation-semantic-svg-source-v1')
        self.assertEqual(native.adapter_id, 'python-pptx-presentation-source-v1')
        self.assertEqual(svg.adapter_id, 'ppt-master-semantic-svg-v1')


if __name__ == '__main__':
    unittest.main()
