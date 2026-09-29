from __future__ import annotations

import sys
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY / "scripts"))

from synthetic_world_r2 import (  # noqa: E402
    PAYLOAD,
    HANDLE,
    SyntheticWorld,
    evaluate_selected_roundtrip,
    find_persistent_roundtrips,
    path_names,
    run_path,
)


class SyntheticWorldR2Tests(unittest.TestCase):
    def test_search_discovers_multiple_structural_roundtrips(self):
        roundtrips = find_persistent_roundtrips(max_len=3)
        self.assertGreaterEqual(len(roundtrips), 2)
        payload_roundtrips = [
            item for item in roundtrips
            if item["sourceType"] == PAYLOAD and item["boundaryType"] == HANDLE
        ]
        self.assertTrue(payload_roundtrips)
        self.assertEqual(path_names(payload_roundtrips[0]["storePath"]), ["encode", "publish"])
        self.assertEqual(path_names(payload_roundtrips[0]["recoverPath"]), ["resolve", "render"])

    def test_external_state_survives_local_forget(self):
        report = evaluate_selected_roundtrip("canary-r2")
        self.assertTrue(report["observations"]["recover_after_local_forget"]["payloadRecovered"])
        self.assertTrue(report["observations"]["recover_in_fresh_session"]["payloadRecovered"])

    def test_r5_admits_composition_only_with_bounded_witnesses(self):
        report = evaluate_selected_roundtrip("canary-r2")
        novelty = report["novelty"]
        self.assertEqual(novelty["verdict"], "CERTIFIED_NOVEL_WITHIN_BOUNDED_POLICY")
        self.assertEqual(len(novelty["witnesses"]), 2)
        self.assertFalse(novelty["authorityGranted"])
        self.assertFalse(novelty["executionAuthorityGranted"])

    def test_world_reset_removes_persistent_handle(self):
        roundtrips = find_persistent_roundtrips(max_len=3)
        selected = next(
            item for item in roundtrips
            if item["sourceType"] == PAYLOAD and item["boundaryType"] == HANDLE
        )
        world = SyntheticWorld()
        handle, _ = run_path(world, selected["storePath"], "canary-r2")
        world.reset()
        with self.assertRaises(KeyError):
            run_path(world, selected["recoverPath"], handle)


if __name__ == "__main__":
    unittest.main()
