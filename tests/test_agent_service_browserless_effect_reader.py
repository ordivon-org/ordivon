from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent_service.local_effect_readers import (
    BrowserlessTurnEffectCoordinate,
    BrowserlessTurnEffectLedgerReader,
)
from agent_service.provider_adapters import (
    EffectLedgerReplaySafetyAdapter,
    ProviderProtocolError,
)


def digest_obj(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class AgentServiceBrowserlessEffectReaderTests(unittest.TestCase):
    def _ledger(self, path: Path) -> sqlite3.Connection:
        db = sqlite3.connect(path)
        db.execute(
            """
            CREATE TABLE turn_effects (
                turn_request_id TEXT PRIMARY KEY,
                prompt_digest TEXT NOT NULL,
                target_coordinate TEXT NOT NULL,
                state TEXT NOT NULL,
                receipt_json TEXT,
                updated_at_ms INTEGER NOT NULL
            )
            """
        )
        db.commit()
        return db

    def _reader(self, path: Path, *, target="https://chatgpt.com/c/abc"):
        coord = BrowserlessTurnEffectCoordinate(
            turn_request_id="turn-1",
            prompt_digest="sha256:" + "1" * 64,
            target_coordinate=target,
        )
        return BrowserlessTurnEffectLedgerReader(path, lambda **kwargs: coord)

    def _snapshot(self, reader):
        return reader.read_replay_snapshot(
            task=SimpleNamespace(id="task-x"),
            envelope=SimpleNamespace(id="deleg-x"),
            source_binding=SimpleNamespace(id="source-x"),
            target_binding=SimpleNamespace(id="target-x"),
            quiescence_proof=SimpleNamespace(id="q-x"),
            source_receipt=None,
            source_observations=(),
        )

    def test_existing_authoritative_table_without_row_proves_no_send_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"turns.db"
            self._ledger(path).close()
            snapshot = self._snapshot(self._reader(path))
            self.assertTrue(snapshot.complete)
            self.assertEqual(snapshot.effects, ())
            verdict = EffectLedgerReplaySafetyAdapter._evaluate_snapshot(
                snapshot,
                expected_task_id="task-x",
                expected_source_binding_id="source-x",
                expected_target_binding_id="target-x",
            )
            self.assertTrue(verdict.safe)
            self.assertEqual(verdict.classification, "NO_EFFECTS")

    def test_missing_ledger_or_table_is_unknown_not_no_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp)/"missing.db"
            snapshot = self._snapshot(self._reader(missing))
            self.assertFalse(snapshot.complete)
            verdict = EffectLedgerReplaySafetyAdapter._evaluate_snapshot(
                snapshot,
                expected_task_id="task-x",
                expected_source_binding_id="source-x",
                expected_target_binding_id="target-x",
            )
            self.assertFalse(verdict.safe)
            self.assertEqual(verdict.classification, "UNKNOWN")

            present = Path(tmp)/"other.db"
            sqlite3.connect(present).close()
            snapshot2 = self._snapshot(self._reader(present))
            self.assertFalse(snapshot2.complete)

    def test_unknown_row_remains_replay_unsafe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"turns.db"
            db = self._ledger(path)
            db.execute(
                "INSERT INTO turn_effects VALUES (?,?,?,?,?,?)",
                ("turn-1","sha256:"+"1"*64,"https://chatgpt.com/c/abc","UNKNOWN",None,1),
            )
            db.commit(); db.close()
            snapshot = self._snapshot(self._reader(path))
            self.assertFalse(snapshot.complete)
            self.assertEqual(snapshot.effects[0].state, "UNKNOWN")
            verdict = EffectLedgerReplaySafetyAdapter._evaluate_snapshot(
                snapshot,
                expected_task_id="task-x",
                expected_source_binding_id="source-x",
                expected_target_binding_id="target-x",
            )
            self.assertFalse(verdict.safe)
            self.assertEqual(verdict.classification, "UNKNOWN")

    def test_completed_row_is_committed_non_idempotent_effect_and_blocks_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"turns.db"
            db = self._ledger(path)
            receipt = {
                "schemaVersion":1,
                "kind":"ordivon.browserless-turn-receipt",
                "turnRequestId":"turn-1",
                "promptDigest":"sha256:"+"1"*64,
                "targetResource":"https://chatgpt.com/c/abc",
                "browserlessEndpointId":"browserless-a",
                "composerCleared":True,
                "generationStarted":True,
                "targetStillBoundAfterSend":True,
                "assistantOutputRead":False,
            }
            receipt["receiptDigest"] = digest_obj(receipt)
            db.execute(
                "INSERT INTO turn_effects VALUES (?,?,?,?,?,?)",
                (
                    "turn-1",
                    "sha256:"+"1"*64,
                    "https://chatgpt.com/c/abc",
                    "COMPLETED",
                    json.dumps(receipt, sort_keys=True),
                    2,
                ),
            )
            db.commit(); db.close()
            snapshot = self._snapshot(self._reader(path))
            self.assertTrue(snapshot.complete)
            self.assertEqual(snapshot.effects[0].state, "COMMITTED")
            self.assertIsNone(snapshot.effects[0].idempotency_key)
            verdict = EffectLedgerReplaySafetyAdapter._evaluate_snapshot(
                snapshot,
                expected_task_id="task-x",
                expected_source_binding_id="source-x",
                expected_target_binding_id="target-x",
            )
            self.assertFalse(verdict.safe)
            self.assertEqual(verdict.classification, "PARTIAL_EFFECTS")

    def test_row_coordinate_or_receipt_identity_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"turns.db"
            db = self._ledger(path)
            db.execute(
                "INSERT INTO turn_effects VALUES (?,?,?,?,?,?)",
                ("turn-1","sha256:"+"2"*64,"https://chatgpt.com/c/abc","UNKNOWN",None,1),
            )
            db.commit(); db.close()
            with self.assertRaises(ProviderProtocolError):
                self._snapshot(self._reader(path))

            path2 = Path(tmp)/"turns2.db"
            db = self._ledger(path2)
            receipt = {
                "schemaVersion":1,
                "kind":"ordivon.browserless-turn-receipt",
                "turnRequestId":"wrong",
                "promptDigest":"sha256:"+"1"*64,
                "targetResource":"https://chatgpt.com/c/abc",
            }
            receipt["receiptDigest"] = digest_obj(receipt)
            db.execute(
                "INSERT INTO turn_effects VALUES (?,?,?,?,?,?)",
                (
                    "turn-1",
                    "sha256:"+"1"*64,
                    "https://chatgpt.com/c/abc",
                    "COMPLETED",
                    json.dumps(receipt),
                    2,
                ),
            )
            db.commit(); db.close()
            with self.assertRaises(ProviderProtocolError):
                self._snapshot(self._reader(path2))


if __name__ == "__main__":
    unittest.main()
