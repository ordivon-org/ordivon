from __future__ import annotations

import unittest

from ordivon_harness.lsp_provider_port import (
    HarnessLspProviderPort,
    LspDiagnosticsObservation,
    LspProviderCapabilities,
    LspProviderIdentity,
    LspProviderReady,
    LspRenameRequest,
    LspWorkspaceEditProposal,
    unicode_column_to_lsp_character,
)

DIGEST = "sha256:" + "1" * 64


class FakeProvider:
    async def initialize(self) -> LspProviderReady:
        return ready()

    async def rename(self, request: LspRenameRequest) -> LspWorkspaceEditProposal:
        return LspWorkspaceEditProposal(
            request_digest=request.digest,
            provider=ready().identity,
            position_encoding="utf-16",
            workspace_edit={"changes": {"file:///demo.py": []}},
        )

    async def drain_diagnostics(self) -> tuple[LspDiagnosticsObservation, ...]:
        return ()

    async def shutdown(self) -> None:
        return None


def ready() -> LspProviderReady:
    return LspProviderReady(
        identity=LspProviderIdentity(
            provider_id="lsp:test",
            implementation="fixture-client",
            version="1.0",
        ),
        capabilities=LspProviderCapabilities(
            position_encoding="utf-16",
            rename=True,
            configuration_requests=True,
            publish_diagnostics=True,
            dynamic_registration=True,
        ),
    )


def request() -> LspRenameRequest:
    return LspRenameRequest(
        relative_path="src/demo.py",
        source_digest=DIGEST,
        language_id="python",
        document_version=3,
        line=2,
        unicode_column=4,
        new_name="renamed",
    )


class LspProviderPortTests(unittest.TestCase):
    def test_ready_and_request_are_canonical_digest_bound(self) -> None:
        self.assertTrue(ready().digest.startswith("sha256:"))
        self.assertTrue(request().digest.startswith("sha256:"))
        self.assertEqual(request().to_dict()["position"], {"line": 2, "unicodeColumn": 4})

    def test_provider_port_exposes_no_mutation_method(self) -> None:
        provider = FakeProvider()
        self.assertIsInstance(provider, HarnessLspProviderPort)
        for name in ("apply", "apply_edit", "write", "workspace_patch"):
            self.assertFalse(hasattr(HarnessLspProviderPort, name))

    def test_direct_workspace_mutation_capability_is_forbidden(self) -> None:
        with self.assertRaisesRegex(ValueError, "forbids direct workspace mutation"):
            LspProviderCapabilities(
                position_encoding="utf-16",
                rename=True,
                configuration_requests=True,
                publish_diagnostics=True,
                dynamic_registration=True,
                direct_workspace_mutation=True,
            )

    def test_workspace_edit_proposal_binds_exact_request_and_provider(self) -> None:
        req = request()
        proposal = LspWorkspaceEditProposal(
            request_digest=req.digest,
            provider=ready().identity,
            position_encoding="utf-16",
            workspace_edit={
                "changes": {
                    "file:///demo.py": [
                        {
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 1},
                            },
                            "newText": "x",
                        }
                    ]
                }
            },
        )
        self.assertEqual(proposal.request_digest, req.digest)
        self.assertTrue(proposal.digest.startswith("sha256:"))

    def test_diagnostics_are_observations_not_authority(self) -> None:
        observation = LspDiagnosticsObservation(
            uri="file:///demo.py",
            document_version=3,
            diagnostics=({"message": "fixture", "severity": 2},),
        )
        encoded = observation.to_dict()
        self.assertEqual(encoded["documentVersion"], 3)
        self.assertEqual(encoded["diagnostics"][0]["message"], "fixture")

    def test_unicode_column_conversion_handles_all_lsp_encodings(self) -> None:
        line = "a😀x"
        self.assertEqual(unicode_column_to_lsp_character(line, 2, "utf-8"), 5)
        self.assertEqual(unicode_column_to_lsp_character(line, 2, "utf-16"), 3)
        self.assertEqual(unicode_column_to_lsp_character(line, 2, "utf-32"), 2)

    def test_invalid_request_and_encoding_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            LspRenameRequest(
                relative_path="../demo.py",
                source_digest=DIGEST,
                language_id="python",
                document_version=0,
                line=1,
                unicode_column=0,
                new_name="x",
            )
        with self.assertRaisesRegex(ValueError, "unsupported LSP position encoding"):
            unicode_column_to_lsp_character("abc", 1, "utf-7")


if __name__ == "__main__":
    unittest.main()
