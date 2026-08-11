from __future__ import annotations

import unittest
from unittest.mock import patch

from ordivon_studio.observatory import (
    CAPABILITIES,
    analyze_snapshot,
    build_matched_pairs,
    collect_apple_music,
    collect_guardian,
    collect_hacker_news,
    title_features,
)


class CulturalObservatoryTest(unittest.TestCase):
    def test_capabilities_keep_live_and_credentialed_sources_distinct(self) -> None:
        statuses = {(item.provider, item.status) for item in CAPABILITIES}
        self.assertIn(("hacker-news", "live"), statuses)
        self.assertIn(("youtube", "capability-only"), statuses)
        self.assertIn(("douyin", "capability-only"), statuses)
        self.assertTrue(all("byte" in item.byte_policy.lower() or "metadata" in item.byte_policy.lower() or "reference" in item.byte_policy.lower() or "aggregated" in item.byte_policy.lower() for item in CAPABILITIES))

    def test_hacker_news_separates_ranked_candidates_from_new_controls(self) -> None:
        values = {
            "https://hacker-news.firebaseio.com/v0/topstories.json": [1, 2],
            "https://hacker-news.firebaseio.com/v0/newstories.json": [2, 3, 4],
            "https://hacker-news.firebaseio.com/v0/item/1.json": {"id": 1, "type": "story", "title": "Ranked: one", "time": 100, "score": 90, "descendants": 12, "url": "https://example.com/a"},
            "https://hacker-news.firebaseio.com/v0/item/2.json": {"id": 2, "type": "story", "title": "Ranked two", "time": 101, "score": 70, "descendants": 8, "url": "https://example.org/b"},
            "https://hacker-news.firebaseio.com/v0/item/3.json": {"id": 3, "type": "story", "title": "Fresh control", "time": 102, "score": 1, "descendants": 0, "url": "https://example.com/c"},
            "https://hacker-news.firebaseio.com/v0/item/4.json": {"id": 4, "type": "story", "title": "Another fresh control", "time": 103, "score": 1, "descendants": 0, "url": "https://example.net/d"},
        }
        with patch("ordivon_studio.observatory._fetch_json", side_effect=lambda url, timeout=20.0: values[url]):
            observations = collect_hacker_news(top_limit=2, new_limit=2)
        self.assertEqual([item["artifact"]["externalId"] for item in observations], ["1", "2", "3", "4"])
        self.assertEqual([item["selection"]["basis"] for item in observations], ["top-ranked", "top-ranked", "new-control", "new-control"])
        self.assertTrue(all(item["acquisition"]["bytesOwned"] is False for item in observations))

    def test_apple_chart_is_rank_signal_not_winner_control(self) -> None:
        document = {
            "feed": {
                "results": [
                    {"id": "a", "name": "Song One", "artistName": "A", "releaseDate": "2026-01-01", "genres": [{"name": "Pop"}], "url": "https://music.apple.com/a"},
                    {"id": "b", "name": "Song Two", "artistName": "B", "releaseDate": "2025-01-01", "genres": [{"name": "Rock"}], "url": "https://music.apple.com/b"},
                ]
            }
        }
        with patch("ordivon_studio.observatory._fetch_json", return_value=document):
            observations = collect_apple_music(limit=2)
        self.assertEqual([item["selection"]["rank"] for item in observations], [1, 2])
        self.assertTrue(all(item["selection"]["basis"] == "chart-ranked" for item in observations))

    def test_guardian_preserves_most_viewed_editorial_and_newest_mechanisms(self) -> None:
        shared = {"type": "article", "sectionId": "world", "sectionName": "World", "webPublicationDate": "2026-08-11T00:00:00Z", "pillarName": "News"}
        response = {
            "response": {
                "mostViewed": [{**shared, "id": "a", "webTitle": "Most viewed", "webUrl": "https://g/a"}],
                "editorsPicks": [{**shared, "id": "b", "webTitle": "Editor pick", "webUrl": "https://g/b"}],
                "results": [
                    {**shared, "id": "a", "webTitle": "Most viewed", "webUrl": "https://g/a"},
                    {**shared, "id": "c", "webTitle": "Newest control", "webUrl": "https://g/c"},
                ],
            }
        }
        with patch("ordivon_studio.observatory._fetch_json", return_value=response):
            observations = collect_guardian(sections=["world"], newest_per_section=2)
        self.assertEqual([item["selection"]["basis"] for item in observations], ["most-viewed", "editors-pick", "newest-control"])
        self.assertEqual(observations[-1]["artifact"]["externalId"], "c")

    def test_matched_analysis_is_explicitly_noncausal(self) -> None:
        def item(provider: str, basis: str, external_id: str, title: str, section: str = "") -> dict:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.studio-cultural-observation",
                "observedAt": "2026-08-11T12:00:00Z",
                "provider": provider,
                "surface": section or "feed",
                "encounterForm": "ranked-link-feed",
                "artifact": {"externalId": external_id, "mediaKind": "article", "title": title, "canonicalUrl": f"https://example.com/{external_id}", "creator": None, "publishedAt": "2026-08-11T10:00:00Z", "descriptors": {"host": "example.com"}},
                "selection": {"basis": basis, "rank": 1, "poolSize": 2},
                "signals": {},
                "context": {"section": section} if section else {},
                "acquisition": {"mode": "metadata-reference", "sourceUrl": "https://source", "bytesOwned": False},
            }
        observations = [
            item("hacker-news", "top-ranked", "h1", "A shorter ranked title"),
            item("hacker-news", "new-control", "h2", "A somewhat longer ordinary control title"),
            item("guardian", "most-viewed", "g1", "World: ranked", "world"),
            item("guardian", "newest-control", "g2", "World ordinary control", "world"),
        ]
        pairs = build_matched_pairs(observations)
        self.assertEqual(len(pairs), 2)
        snapshot = {"schemaVersion": 1, "kind": "ordivon.studio-cultural-snapshot", "snapshotDigest": "sha256:test", "countsByProvider": {"hacker-news": 2, "guardian": 2}, "failures": [], "observations": observations}
        report = analyze_snapshot(snapshot, clusters=2)
        self.assertEqual(report["matchedControls"]["pairCount"], 2)
        self.assertTrue(any("do not identify causal" in line for line in report["interpretationBoundary"]))
        self.assertEqual(title_features(observations[0])["hasColon"], 0.0)
        self.assertEqual(title_features(observations[2])["hasColon"], 1.0)


if __name__ == "__main__":
    unittest.main()
