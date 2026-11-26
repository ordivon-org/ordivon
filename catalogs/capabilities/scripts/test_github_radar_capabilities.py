"""Behavior tests for discovery, normalization and the real CLI contract."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import mock

from catalogs.capabilities.scripts.github_radar.history import previous_repositories
from catalogs.capabilities.scripts.github_radar.normalization import normalize
from catalogs.capabilities.scripts.github_radar.parser import parse_trending
from catalogs.capabilities.scripts.github_radar.provider import (
    fetch_json,
    live_observation,
)

CLI = Path(__file__).resolve().parent / "github_radar_incremental.py"


def observation() -> dict:
    return {
        "kind": "ordivon.github-trending-observation-r1",
        "snapshotDay": "2026-11-21",
        "observedAt": "2026-11-21T00:00:00+00:00",
        "origin": "github-official-trending-pages",
        "windows": [{
            "window": "daily",
            "sourceUrl": "https://github.com/trending?since=daily",
            "retrievedAt": "2026-11-21T00:00:00+00:00",
            "sourceBodySha256": "sha256:actual-observation",
            "entries": [{"repo": "example/safe", "newStars": 17, "sourceWindowLabel": "today"}],
        }],
        "windowFailures": {"weekly": "source temporarily unavailable"},
        "repositories": {"example/safe": {"apiStatus": "FAILED", "note": "rate limited"}},
    }


class GitHubRadarContracts(unittest.TestCase):
    def test_html_void_elements_do_not_drop_real_trending_cards(self) -> None:
        html = ('<article class="Box-row"><h2><a href="/example/safe">'
                '<img src="/avatar.png">example/safe</a></h2>'
                '<p> 1,200 stars today </p></article>')
        result = parse_trending(html, "daily")
        self.assertEqual(result, [{
            "repo": "example/safe", "newStars": 1200, "sourceWindowLabel": "today",
        }])
        with self.assertRaises(ValueError):
            parse_trending('<article class="Box-row"><h2>Unparseable</h2></article>', "daily")

    def test_partial_coverage_and_api_failure_remain_explicit(self) -> None:
        output = normalize(observation(), set())
        self.assertFalse(output["sourceCoverage"]["complete"])
        self.assertEqual(output["sourceCoverage"]["failedWindows"], ["weekly"])
        self.assertEqual(output["sourceCoverage"]["unobservedWindows"], ["monthly"])
        candidate = output["candidates"][0]
        self.assertIsNone(candidate["totalStars"])
        self.assertEqual(candidate["apiStatus"], "FAILED")
        self.assertEqual(candidate["apiFailureNote"], "rate limited")
        self.assertEqual(candidate["adoptionStanding"], "DISCOVERY_ONLY")

    def test_corrupted_window_or_star_facts_fail_instead_of_fabricating(self) -> None:
        mutations = []
        invalid = deepcopy(observation())
        invalid["windows"][0]["sourceUrl"] = "https://example.invalid/fake"
        mutations.append(invalid)
        invalid = deepcopy(observation())
        invalid["windows"][0]["entries"][0]["newStars"] = True
        mutations.append(invalid)
        invalid = deepcopy(observation())
        invalid["windows"].append(deepcopy(invalid["windows"][0]))
        mutations.append(invalid)
        invalid = deepcopy(observation())
        invalid["windowFailures"]["daily"] = "fake failure on observed window"
        mutations.append(invalid)
        for altered in mutations:
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                normalize(altered, set())

    def test_history_seven_day_window_and_real_replay_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "history"
            history.mkdir()
            for day, name in (("2026-11-15", "recent"), ("2026-11-12", "stale")):
                (history / (name + ".json")).write_text(json.dumps({
                    "kind": "ordivon.github-radar-candidates-r1",
                    "snapshotDay": day,
                    "candidates": [{"repo": "example/safe"}],
                }), encoding="utf-8")
            source = root / "observation.json"
            destination = root / "result.json"
            source.write_text(json.dumps(observation()), encoding="utf-8")
            self.assertEqual(previous_repositories(history, date(2026, 11, 21), destination), {"example/safe"})
            result = subprocess.run([
                sys.executable, str(CLI), "--input", str(source),
                "--history-dir", str(history), "--output", str(destination),
            ], capture_output=True, text=True, timeout=15, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = json.loads(destination.read_text(encoding="utf-8"))
            self.assertTrue(saved["candidates"][0]["repeatedWithin7Days"])
            self.assertEqual(saved["candidates"][0]["recommendationDisposition"], "REVIEW_CHANGE_BEFORE_REPEAT")
            self.assertEqual(json.loads(result.stdout)["candidateCount"], 1)

    def test_provider_failure_does_not_become_empty_success(self) -> None:
        failure = subprocess.CompletedProcess(["curl"], 22, b"", b"source denied")
        with (
            mock.patch("catalogs.capabilities.scripts.github_radar.provider.subprocess.run", return_value=failure),
            self.assertRaisesRegex(RuntimeError, "all official GitHub Trending windows failed"),
        ):
                live_observation(5)

    def test_metadata_failure_cannot_claim_absent_repository(self) -> None:
        failure = subprocess.CompletedProcess(["gh"], 1, "", "rate limited")
        with mock.patch("catalogs.capabilities.scripts.github_radar.provider.subprocess.run", return_value=failure):
            output = fetch_json("example/safe")
        self.assertEqual(output["apiStatus"], "FAILED")
        self.assertIsNone(output["totalStars"])
        self.assertIn("rate limited", output["note"])


if __name__ == "__main__":
    unittest.main()
