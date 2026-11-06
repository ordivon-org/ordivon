"""External LEGO evidence and GitHub radar consumer-contract tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "catalogs/capabilities/scripts"))
from check_external_lego_evidence import check
from github_radar_incremental import normalize, previous_repositories, parse_trending


class EvidenceTests(unittest.TestCase):
    def test_current_bounded_worktrunk_chain(self):
        packet = ROOT / "catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json"
        self.assertEqual(check(ROOT, packet), [])

    def test_negative_fake_adoption_and_reference(self):
        original = json.loads((ROOT / "catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "invalid.json"
            original["decision"] = "ADOPT_SCOPED"
            original["references"]["provider"] = "../../etc/passwd"
            original["standing"] = "ADMITTED"
            p.write_text(json.dumps(original), encoding="utf-8")
            errors = check(ROOT, p)
        self.assertTrue(any("approval" in e for e in errors))
        self.assertTrue(any("missing 11" in e for e in errors))
        self.assertTrue(any("missing or escaping" in e for e in errors))


class WorktrunkConsumerProjectionTests(unittest.TestCase):
    def test_exact_porcelain_projection(self):
        from compare_worktrunk_owner_consumer import projected_porcelain
        snapshot = {"items": [
            {"branch": "main", "head": {"sha": "1" * 40},
             "worktree": {"path": "/tmp/example-main", "detached": False}},
            {"branch": None, "head": {"sha": "2" * 40},
             "worktree": {"path": "/tmp/example-linked", "detached": True}},
        ]}
        expected = ("worktree /tmp/example-main\nHEAD " + "1" * 40 +
                    "\nbranch refs/heads/main\n\n" +
                    "worktree /tmp/example-linked\nHEAD " + "2" * 40 +
                    "\ndetached\n\n").encode()
        self.assertEqual(projected_porcelain(snapshot, native_metadata=b""), expected)

    def test_prunable_metadata_fails_closed(self):
        from compare_worktrunk_owner_consumer import projected_porcelain
        snapshot = {"items": [{"branch": "main", "head": {"sha": "1" * 40},
                               "worktree": {"path": "/tmp/main", "detached": False}}]}
        with self.assertRaisesRegex(ValueError, "prunable"):
            projected_porcelain(snapshot, native_metadata=b"prunable gitdir missing\n")

    def test_ambiguous_candidate_denied(self):
        from compare_worktrunk_owner_consumer import projected_porcelain
        entry = {"branch": "main", "head": {"sha": "1" * 40},
                 "worktree": {"path": "/tmp/main", "detached": False}}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            projected_porcelain({"items": [entry, entry]}, native_metadata=b"")
        with self.assertRaisesRegex(ValueError, "HEAD"):
            projected_porcelain({"items": [{"branch": "main", "head": {"sha": "x"},
                                            "worktree": {"path": "/tmp/main", "detached": False}}]},
                                native_metadata=b"")


class RadarTests(unittest.TestCase):
    def example(self):
        return {"kind": "ordivon.github-trending-observation-r1", "snapshotDay": "2026-11-06",
                "observedAt": "2026-11-06T05:00:00Z", "origin": "github-official-trending-pages",
                "windows": [
                    {"window": w, "sourceUrl": "https://github.com/trending?since=" + w,
                     "retrievedAt": "2026-11-06T05:00:00Z",
                     "entries": [{"repo": "max-sixty/worktrunk", "newStars": n,
                                  "sourceWindowLabel": lab}]}
                    for w, n, lab in [("daily",546,"today"),("weekly",1802,"this week"),("monthly",4300,"this month")]],
                "repositories": {"max-sixty/worktrunk": {"totalStars":11604, "apiStatus":"OK",
                                                         "licenseMetadata":"NOASSERTION"}}}

    def test_window_counts_and_total_are_separate(self):
        output = normalize(self.example(), set())
        item = output["candidates"][0]
        self.assertEqual(item["totalStars"], 11604)
        self.assertEqual([x["stars"] for x in item["officialTrending"]],[546,1802,4300])
        self.assertEqual(item["adoptionStanding"],"DISCOVERY_ONLY")

    def test_wrong_window_rejected(self):
        data = self.example()
        data["windows"][0]["entries"][0]["sourceWindowLabel"]="this week"
        with self.assertRaises(ValueError):
            normalize(data,set())

    def test_seven_day_repeat_not_auto_adopt(self):
        data=self.example()
        result=normalize(data,{"max-sixty/worktrunk"})
        self.assertTrue(result["candidates"][0]["repeatedWithin7Days"])
        self.assertEqual(result["candidates"][0]["recommendationDisposition"],"REVIEW_CHANGE_BEFORE_REPEAT")

    def test_official_markup_parser(self):
        h='<article class="Box-row"><h2><a href="/max-sixty/worktrunk">Worktrunk</a></h2><span>546 stars today</span></article>'
        self.assertEqual(parse_trending(h,"daily")[0]["newStars"],546)

    def test_history_has_horizon_and_ignores_untrusted_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            content={"kind":"ordivon.github-radar-candidates-r1","snapshotDay":"2026-11-03",
                     "candidates":[{"repo":"max-sixty/worktrunk"}]}
            (d/"first.json").write_text(json.dumps(content))
            (d/"invalid.json").write_text("{")
            self.assertEqual(previous_repositories(d,__import__("datetime").date(2026,11,6),d/"out.json"),
                             {"max-sixty/worktrunk"})


if __name__ == "__main__":
    unittest.main()
