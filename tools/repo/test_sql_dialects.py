"""Deliberate counterexamples to the SQL source/dialect gate."""
import unittest

from tools.repo.check_sql_dialects import (
    OSQUERY_DEFAULT_TIMEOUT_SECONDS,
    OSQUERY_TIMEOUT_SECONDS,
    classify,
)


class SQLDialectBoundaryTests(unittest.TestCase):
    def test_known_sql_are_classified(self):
        self.assertEqual(classify("services/runtime/crates/ordivon-runtime-core/migrations/runtime/0001_runtime.sql"), "sqlite")
        self.assertEqual(classify("services/runtime/crates/ordivon-runtime-core/src/runtime/attempt_supervisor_owner_storage.sql"), "sqlite")
        self.assertEqual(classify("platform/workstation/inventory/queries/uptime.sql"), "osquery")
        self.assertEqual(classify("meta/next/scripts/experimental_episode_r5c_source_r1.sql"), "postgresql")

    def test_full_host_package_queries_are_bounded_and_not_downgraded(self):
        self.assertEqual(OSQUERY_TIMEOUT_SECONDS["python_packages.sql"], 120)
        self.assertEqual(OSQUERY_TIMEOUT_SECONDS["npm_packages.sql"], 120)
        self.assertEqual(OSQUERY_DEFAULT_TIMEOUT_SECONDS, 30)
        self.assertLessEqual(max(OSQUERY_TIMEOUT_SECONDS.values()), 120)

    def test_unknown_sql_is_not_certified(self):
        for name in ("domains/game/later.sql", "services/runtime/crates/ordivon-runtime-core/src/runtime/bad.sql"):
            with self.subTest(name=name):
                self.assertIsNone(classify(name))


if __name__ == "__main__":
    unittest.main()
