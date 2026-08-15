from __future__ import annotations
import unittest
from ordivon_studio.figma_provider import figma_provider_surface, route_figma_operation

class FigmaProviderTests(unittest.TestCase):
    def test_shared_context_prefers_current_desktop_without_claiming_truth(self):
        route=route_figma_operation('design.context.read',desktop_state='available',remote_state='available')
        self.assertEqual(route.disposition,'ready'); self.assertEqual(route.backend,'figma-desktop')
        self.assertFalse(route.studioOwnsProviderTruth); self.assertTrue(route.mcpIsProviderTransport)
    def test_remote_only_operation_never_falls_back_to_desktop(self):
        route=route_figma_operation('design.file.create',desktop_state='available',remote_state='unavailable')
        self.assertEqual(route.disposition,'unavailable'); self.assertIsNone(route.backend); self.assertEqual(route.providerTool,'create_new_file')
    def test_unknown_remote_auth_is_authority_boundary_not_ready(self):
        route=route_figma_operation('design.canvas.write',desktop_state='available',remote_state='unknown')
        self.assertEqual(route.disposition,'requires-authority'); self.assertEqual(route.backend,'figma-remote')
        self.assertIn('oauth',route.authorityRequired.lower())
    def test_selection_is_desktop_native_and_remote_does_not_substitute(self):
        route=route_figma_operation('design.selection.read',desktop_state='unavailable',remote_state='available')
        self.assertEqual(route.disposition,'unavailable')
    def test_surface_contains_no_credentials_and_marks_remote_broadest(self):
        surface=figma_provider_surface(); self.assertTrue(surface['backends']['figma-remote']['broadestFeatureSet'])
        self.assertFalse(surface['backends']['figma-desktop']['broadestFeatureSet'])
        text=str(surface).lower(); self.assertNotIn('access_token',text); self.assertNotIn('client_secret',text)
    def test_unknown_operation_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'unsupported Studio Figma operation'): route_figma_operation('figma.anything')

if __name__=='__main__': unittest.main()
