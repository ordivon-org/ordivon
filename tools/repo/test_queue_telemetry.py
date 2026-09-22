import unittest

from queue_telemetry import ProviderSnapshot, analyze, seconds


class QueueTelemetryTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(seconds("2026-09-22T12:00:00Z", "2026-09-22T12:00:07Z"), 7)

    def test_provider_projection_metrics(self):
        snapshot = ProviderSnapshot(
            repository="o/r",
            pulls=[
                {"number": 7, "merged_at": "2026-09-22T12:00:40Z"},
                {"number": 8, "merged_at": "2026-09-22T12:01:00Z"},
            ],
            timelines={
                "7": [
                    {"event": "added_to_merge_queue", "created_at": "2026-09-22T12:00:00Z"},
                    {"event": "removed_from_merge_queue", "created_at": "2026-09-22T12:00:40Z"},
                ],
                "8": [
                    {"event": "added_to_merge_queue", "created_at": "2026-09-22T12:00:10Z"},
                    {"event": "removed_from_merge_queue", "created_at": "2026-09-22T12:01:00Z"},
                ],
            },
            merge_group_runs=[
                {
                    "id": 70, "head_branch": "gh-readonly-queue/main/pr-7-base",
                    "head_sha": "a", "created_at": "2026-09-22T12:00:05Z",
                    "conclusion": "success",
                },
                {
                    "id": 80, "head_branch": "gh-readonly-queue/main/pr-8-base",
                    "head_sha": "b", "created_at": "2026-09-22T12:00:20Z",
                    "conclusion": "failure",
                },
                {
                    "id": 81, "head_branch": "gh-readonly-queue/main/pr-8-base2",
                    "head_sha": "c", "created_at": "2026-09-22T12:00:30Z",
                    "conclusion": "success",
                },
            ],
            jobs={
                "70": [{"name": "root-verification", "created_at": "2026-09-22T12:00:06Z",
                        "started_at": "2026-09-22T12:00:08Z", "completed_at": "2026-09-22T12:00:30Z"}],
                "80": [{"name": "root-verification", "created_at": "2026-09-22T12:00:21Z",
                        "started_at": "2026-09-22T12:00:22Z", "completed_at": "2026-09-22T12:00:27Z"}],
                "81": [{"name": "root-verification", "created_at": "2026-09-22T12:00:31Z",
                        "started_at": "2026-09-22T12:00:32Z", "completed_at": "2026-09-22T12:00:50Z"}],
            },
        )
        result = analyze(snapshot)
        self.assertFalse(result["authority"]["durableLocalQueueState"])
        self.assertEqual(result["coverage"]["queueAttributedPullRequests"], 2)
        self.assertEqual(result["metrics"]["observedPeakQueueDepthLowerBound"], 2)
        self.assertEqual(result["metrics"]["unsuccessfulMergeGroupRuns"], 1)
        self.assertEqual(result["metrics"]["observedWastedVerificationSeconds"], 5)
        self.assertEqual(result["metrics"]["queueDispatchSeconds"]["median"], 12.5)
        by_pr = {x["pr"]: x for x in result["observations"]}
        self.assertEqual(by_pr[7]["verificationSeconds"], 22)
        self.assertEqual(by_pr[8]["mergeGroupRuns"], 2)
        self.assertEqual(result["pressureGate"]["adaptiveSpeculation"], "INSUFFICIENT_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
