from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workstation.input_authority_ingress import IngressConflict, IngressError, _state_paths, ingest


class FakeFetcher:
    def __init__(self, payload: bytes, *, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.calls = 0
        self.sources: list[str] = []

    def fetch(self, source: str, target: Path, *, max_bytes: int) -> None:
        self.calls += 1
        self.sources.append(source)
        if self.error is not None:
            raise self.error
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.payload)


class InputAuthorityIngressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.authority = self.root / "authority"
        self.authority.mkdir()
        self.state = self.root / "state"
        self.payload = b"exact-golden-bytes\x00\x01"
        self.digest = "sha256:" + hashlib.sha256(self.payload).hexdigest()
        self.config = {
            "schemaVersion": 1,
            "stateDir": str(self.state),
            "maxBytes": 1024,
            "carriers": {"artifact-drive": {"kind": "rclone", "sourcePrefix": "drive:Ordivon Artifact Ingress/golden-r1/"}},
            "authorities": {"artifact-golden-r1": {"root": str(self.authority)}},
        }
        self.request = {
            "schemaVersion": 1,
            "requestId": "golden-slide-01-v1",
            "carrier": "artifact-drive",
            "sourceObject": "pdu-sdu/34x10/slide-01.jpeg",
            "sourceProvenance": {
                "provider": "google-drive",
                "providerFileId": "drive-file-01",
                "providerVersion": "modified-at-v1",
                "libraryFileId": "library-file-01",
                "libraryVersion": "1",
                "parentObjectDigest": "sha256:" + "1" * 64,
                "member": "ppt/media/image-1-1.jpeg",
            },
            "expectedSha256": self.digest,
            "authority": "artifact-golden-r1",
            "relativeObject": "pdu-sdu/34x10/slide-01.jpeg",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def destination(self) -> Path:
        return self.authority / "pdu-sdu/34x10/slide-01.jpeg"


    def local_stage_config(self, source_root: Path) -> dict:
        return {
            **self.config,
            "carriers": {"runtime-stage": {"kind": "local-stage", "sourceRoot": str(source_root)}},
        }

    def local_stage_request(self) -> dict:
        return {**self.request, "requestId": "local-stage-slide-01", "carrier": "runtime-stage"}


    def test_reconcile_only_freezes_intent_without_fetching_source(self) -> None:
        class ForbiddenFetcher:
            def fetch(self, source: str, target: Path, *, max_bytes: int) -> None:
                raise AssertionError("reconcile-only must never fetch source bytes")

        result = ingest(
            self.config,
            self.request,
            fetcher=ForbiddenFetcher(),
            reconcile_only=True,
        )
        self.assertEqual(result["standing"], "SOURCE_REQUIRED")
        self.assertEqual(result["truthRole"], "source-fetch-admission-only-not-byte-materialization")
        self.assertFalse(self.destination().exists())
        intent_path, receipt_path, staging_path = _state_paths(self.state, self.request["requestId"])
        self.assertTrue(intent_path.is_file())
        self.assertFalse(receipt_path.exists())
        self.assertFalse(staging_path.exists())

        committed = ingest(self.config, self.request, fetcher=FakeFetcher(self.payload))
        self.assertEqual(committed["commitStanding"], "COMMITTED_NEW")
        self.assertEqual(self.destination().read_bytes(), self.payload)

    def test_reconcile_only_recovers_exact_destination_without_fetch(self) -> None:
        class ForbiddenFetcher:
            def fetch(self, source: str, target: Path, *, max_bytes: int) -> None:
                raise AssertionError("exact destination reconciliation must not fetch")

        self.destination().parent.mkdir(parents=True, exist_ok=True)
        self.destination().write_bytes(self.payload)
        result = ingest(
            self.config,
            self.request,
            fetcher=ForbiddenFetcher(),
            reconcile_only=True,
        )
        self.assertEqual(result["commitStanding"], "COMMITTED_RECOVERED")
        self.assertTrue(result["recoveredAfterResponseLoss"])

    def test_local_stage_exact_commit_reads_only_configured_root(self) -> None:
        source_root = self.root / "runtime-stage"
        source = source_root / "pdu-sdu/34x10/slide-01.jpeg"
        source.parent.mkdir(parents=True)
        source.write_bytes(self.payload)
        receipt = ingest(self.local_stage_config(source_root), self.local_stage_request())
        self.assertEqual(receipt["commitStanding"], "COMMITTED_NEW")
        self.assertEqual(self.destination().read_bytes(), self.payload)
        self.assertEqual(receipt["source"]["provenanceStanding"], "DECLARED_UNVERIFIED")

    def test_local_stage_source_symlink_is_rejected(self) -> None:
        source_root = self.root / "runtime-stage"
        nested = source_root / "pdu-sdu/34x10"
        nested.mkdir(parents=True)
        outside = self.root / "outside-source"
        outside.write_bytes(self.payload)
        os.symlink(outside, nested / "slide-01.jpeg")
        with self.assertRaises(IngressError):
            ingest(self.local_stage_config(source_root), self.local_stage_request())
        self.assertFalse(self.destination().exists())

    def test_local_stage_parent_symlink_is_rejected(self) -> None:
        source_root = self.root / "runtime-stage"
        source_root.mkdir()
        outside = self.root / "outside-dir"
        (outside / "34x10").mkdir(parents=True)
        (outside / "34x10/slide-01.jpeg").write_bytes(self.payload)
        os.symlink(outside, source_root / "pdu-sdu")
        with self.assertRaises(IngressError):
            ingest(self.local_stage_config(source_root), self.local_stage_request())
        self.assertFalse(self.destination().exists())

    def test_local_stage_root_must_be_absolute_and_real_at_fetch(self) -> None:
        bad = {**self.config, "carriers": {"runtime-stage": {"kind": "local-stage", "sourceRoot": "relative/stage"}}}
        with self.assertRaises(IngressError):
            ingest(bad, self.local_stage_request())
        real = self.root / "real-stage"
        real.mkdir()
        link = self.root / "stage-link"
        os.symlink(real, link)
        with self.assertRaises(IngressError):
            ingest(self.local_stage_config(link), self.local_stage_request())

    def test_local_stage_oversize_remains_fail_closed(self) -> None:
        source_root = self.root / "runtime-stage"
        source = source_root / "pdu-sdu/34x10/slide-01.jpeg"
        source.parent.mkdir(parents=True)
        source.write_bytes(self.payload)
        config = {**self.local_stage_config(source_root), "maxBytes": 4}
        receipt = ingest(config, self.local_stage_request())
        self.assertEqual(receipt["commitStanding"], "REJECTED_OVERSIZED")
        self.assertFalse(self.destination().exists())

    def test_new_commit_and_duplicate_replay_are_exact_and_idempotent(self) -> None:
        fetcher = FakeFetcher(self.payload)
        first = ingest(self.config, self.request, fetcher=fetcher)
        second = ingest(self.config, self.request, fetcher=fetcher)
        self.assertEqual(first["commitStanding"], "COMMITTED_NEW")
        self.assertEqual(second, first)
        self.assertEqual(fetcher.calls, 1)
        self.assertEqual(self.destination().read_bytes(), self.payload)
        self.assertEqual(first["observedSha256"], self.digest)

    def test_digest_mismatch_fails_closed_without_destination(self) -> None:
        receipt = ingest(self.config, self.request, fetcher=FakeFetcher(b"changed"))
        self.assertEqual(receipt["commitStanding"], "REJECTED_SOURCE_DIGEST")
        self.assertFalse(self.destination().exists())

    def test_oversized_input_fails_closed(self) -> None:
        config = {**self.config, "maxBytes": 4}
        receipt = ingest(config, self.request, fetcher=FakeFetcher(self.payload))
        self.assertEqual(receipt["commitStanding"], "REJECTED_OVERSIZED")
        self.assertFalse(self.destination().exists())

    def test_traversal_and_absolute_destination_are_rejected_before_intent(self) -> None:
        for value in ("../escape", "/tmp/escape", "a/../../escape"):
            request = {**self.request, "requestId": "bad-" + hashlib.sha256(value.encode()).hexdigest()[:8], "relativeObject": value}
            with self.assertRaises(IngressError):
                ingest(self.config, request, fetcher=FakeFetcher(self.payload))
        self.assertFalse((self.root / "escape").exists())

    def test_existing_exact_destination_is_reconciled_without_fetch(self) -> None:
        self.destination().parent.mkdir(parents=True)
        self.destination().write_bytes(self.payload)
        fetcher = FakeFetcher(b"must-not-be-read")
        receipt = ingest(self.config, self.request, fetcher=fetcher)
        self.assertEqual(receipt["commitStanding"], "COMMITTED_RECOVERED")
        self.assertTrue(receipt["recoveredAfterResponseLoss"])
        self.assertEqual(fetcher.calls, 0)

    def test_existing_conflicting_destination_is_never_overwritten(self) -> None:
        self.destination().parent.mkdir(parents=True)
        self.destination().write_bytes(b"foreign")
        fetcher = FakeFetcher(self.payload)
        receipt = ingest(self.config, self.request, fetcher=fetcher)
        self.assertEqual(receipt["commitStanding"], "REJECTED_DESTINATION_CONFLICT")
        self.assertEqual(fetcher.calls, 0)
        self.assertEqual(self.destination().read_bytes(), b"foreign")

    def test_same_request_id_with_changed_request_conflicts(self) -> None:
        fetcher = FakeFetcher(self.payload)
        ingest(self.config, self.request, fetcher=fetcher)
        changed = {**self.request, "sourceObject": "pdu-sdu/34x10/slide-02.jpeg"}
        with self.assertRaises(IngressConflict):
            ingest(self.config, changed, fetcher=fetcher)

    def test_source_version_drift_with_changed_bytes_is_rejected(self) -> None:
        drifted = {**self.request, "requestId": "drift-v2", "sourceProvenance": {**self.request["sourceProvenance"], "providerVersion": "modified-at-v2"}}
        receipt = ingest(self.config, drifted, fetcher=FakeFetcher(b"new-provider-version"))
        self.assertEqual(receipt["commitStanding"], "REJECTED_SOURCE_DIGEST")

    def test_symlink_parent_is_rejected_and_target_untouched(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        os.symlink(outside, self.authority / "pdu-sdu")
        receipt = ingest(self.config, self.request, fetcher=FakeFetcher(self.payload))
        self.assertEqual(receipt["commitStanding"], "REJECTED_DESTINATION_UNSAFE")
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_destination_is_rejected(self) -> None:
        self.destination().parent.mkdir(parents=True)
        outside = self.root / "outside-file"
        outside.write_bytes(b"do-not-touch")
        os.symlink(outside, self.destination())
        receipt = ingest(self.config, self.request, fetcher=FakeFetcher(self.payload))
        self.assertEqual(receipt["commitStanding"], "REJECTED_DESTINATION_UNSAFE")
        self.assertEqual(outside.read_bytes(), b"do-not-touch")

    def test_response_loss_after_commit_is_recovered_from_intent_and_destination(self) -> None:
        # Simulate an earlier process that durably recorded intent and atomically committed bytes
        # but disappeared before writing its final receipt.
        fetcher = FakeFetcher(self.payload)
        first = ingest(self.config, self.request, fetcher=fetcher)
        receipts = list((self.state / "requests").glob("*.receipt.json"))
        self.assertEqual(len(receipts), 1)
        receipts[0].unlink()
        recovered = ingest(self.config, self.request, fetcher=FakeFetcher(b"must-not-fetch"))
        self.assertEqual(first["observedSha256"], recovered["observedSha256"])
        self.assertEqual(recovered["commitStanding"], "COMMITTED_RECOVERED")
        self.assertTrue(recovered["recoveredAfterResponseLoss"])

    def test_partial_local_commit_interruption_can_retry_without_overwrite(self) -> None:
        fetcher = FakeFetcher(self.payload)
        with mock.patch("workstation.input_authority_ingress.os.link", side_effect=OSError(errno.EIO, "simulated interruption")):
            with self.assertRaises(OSError):
                ingest(self.config, self.request, fetcher=fetcher)
        self.assertFalse(self.destination().exists())
        recovered = ingest(self.config, self.request, fetcher=fetcher)
        self.assertEqual(recovered["commitStanding"], "COMMITTED_NEW")
        self.assertEqual(self.destination().read_bytes(), self.payload)

    def test_secretish_provenance_fields_are_rejected_and_not_persisted(self) -> None:
        request = {**self.request, "requestId": "secret-reject", "sourceProvenance": {**self.request["sourceProvenance"], "accessToken": "TOP-SECRET"}}
        with self.assertRaises(IngressError):
            ingest(self.config, request, fetcher=FakeFetcher(self.payload))
        persisted = "".join(path.read_text(errors="ignore") for path in self.state.rglob("*.json")) if self.state.exists() else ""
        self.assertNotIn("TOP-SECRET", persisted)

    def test_fetcher_error_text_is_not_persisted(self) -> None:
        secret = "BEARER-DO-NOT-PERSIST"
        fetcher = FakeFetcher(self.payload, error=IngressError(secret))
        with self.assertRaises(IngressError):
            ingest(self.config, self.request, fetcher=fetcher)
        persisted = "".join(path.read_text(errors="ignore") for path in self.state.rglob("*.json"))
        self.assertNotIn(secret, persisted)

    def test_source_payload_bytes_are_never_persisted_in_ledger(self) -> None:
        ingest(self.config, self.request, fetcher=FakeFetcher(self.payload))
        persisted = b"".join(path.read_bytes() for path in self.state.rglob("*.json"))
        self.assertNotIn(self.payload, persisted)

    def test_exact_destination_race_converges_without_overwrite(self) -> None:
        fetcher = FakeFetcher(self.payload)

        def concurrent_exact(*_args, **_kwargs):
            self.destination().parent.mkdir(parents=True, exist_ok=True)
            self.destination().write_bytes(self.payload)
            raise FileExistsError(errno.EEXIST, "simulated exact concurrent commit")

        with mock.patch("workstation.input_authority_ingress.os.link", side_effect=concurrent_exact):
            receipt = ingest(self.config, self.request, fetcher=fetcher)
        self.assertEqual(receipt["commitStanding"], "COMMITTED_EXISTING")
        self.assertEqual(self.destination().read_bytes(), self.payload)


if __name__ == "__main__":
    unittest.main()
