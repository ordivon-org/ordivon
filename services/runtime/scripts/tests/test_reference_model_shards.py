"""Native Runtime extended-property shard planner and independent result oracle."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_reference_model_shards import plan_shards, qualifies_result, select_test_executable


class ReferenceModelShardContract(unittest.TestCase):
    def test_exactly_512_distinct_seeded_cases_are_allocated(self):
        plan = plan_shards(8)
        self.assertEqual(len(plan), 8)
        self.assertEqual(sum(item["cases"] for item in plan), 512)
        self.assertEqual(len({item["seed"] for item in plan}), 8)
        self.assertEqual([item["index"] for item in plan], list(range(8)))

    def test_disallow_partial_or_zero_shards(self):
        for total in (0, 1, 3, 5, 7, 9, 513):
            with self.subTest(total=total), self.assertRaises(ValueError):
                plan_shards(total)

    def test_binary_selection_is_exact_and_requires_one_test_artifact(self):
        import json
        good = json.dumps({
            "reason": "compiler-artifact",
            "target": {"name": "ordivon_runtime_core", "kind": ["lib"]},
            "profile": {"test": True},
            "executable": "/tmp/owner-target/debug/deps/ordivon_runtime_core-proof",
        })
        self.assertEqual(
            select_test_executable(good, "/tmp/owner-target"),
            "/tmp/owner-target/debug/deps/ordivon_runtime_core-proof",
        )
        with self.assertRaises(ValueError):
            select_test_executable("", "/tmp/owner-target")
        with self.assertRaises(ValueError):
            select_test_executable(good, "/tmp/other-target")

    def test_qualifier_requires_one_executed_passing_test(self):
        good = "running 1 test\n...\ntest result: ok. 1 passed; 0 failed; 0 ignored\n"
        self.assertTrue(qualifies_result(0, good))
        self.assertFalse(qualifies_result(0, "running 0 tests\ntest result: ok. 0 passed; 0 failed\n"))
        self.assertFalse(qualifies_result(1, good))
        self.assertFalse(qualifies_result(0, "test result: FAILED. 0 passed; 1 failed\n"))


if __name__ == "__main__":
    unittest.main()
