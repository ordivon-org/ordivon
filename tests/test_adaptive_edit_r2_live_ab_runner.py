from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_adaptive_edit_r2_live_ab.py"
spec = importlib.util.spec_from_file_location("adaptive_edit_r2_live_ab", SCRIPT)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class AdaptiveEditR2LiveABRunnerTests(unittest.TestCase):
    def test_treatments_expose_exactly_one_codec_schema(self) -> None:
        exact = runner.treatment_edit_definition("exact-replacement-v1")
        anchored = runner.treatment_edit_definition("anchored-line-v1")
        self.assertEqual(
            exact.input_schema["properties"]["codec"]["const"],
            "exact-replacement-v1",
        )
        self.assertIn("oldText", exact.input_schema["properties"])
        self.assertNotIn("startAnchor", exact.input_schema["properties"])
        self.assertEqual(
            anchored.input_schema["properties"]["codec"]["const"],
            "anchored-line-v1",
        )
        self.assertIn("startAnchor", anchored.input_schema["properties"])
        self.assertNotIn("oldText", anchored.input_schema["properties"])

    def test_memory_runtime_applies_digest_fenced_runtime_patch_shape(self) -> None:
        runtime = runner.MemoryRuntime()
        before = runtime.files["allocation.py"]
        old = "    return [(total * weight) // weight_total for weight in weights]"
        start = before.index(old)
        prefix = before[:start]
        line = prefix.count("\n") + 1
        column = len(prefix.rsplit("\n", 1)[-1])
        request = {
            "schemaVersion": 1,
            "clientRequestId": "request:test-live-ab-memory-runtime",
            "workspaceId": "ws-live-ab",
            "files": [
                {
                    "relativePath": "allocation.py",
                    "expectedDigest": runner.sha(before),
                    "edits": [
                        {
                            "range": {
                                "start": {"line": line, "column": column},
                                "end": {"line": line, "column": column + len(old)},
                            },
                            "expectedText": old,
                            "replacement": "    return [0 for _ in weights]",
                        }
                    ],
                }
            ],
            "maxDiffBytes": 4096,
        }
        receipt = runtime.call_tool("workspace.patch", request)
        self.assertEqual(receipt["clientRequestId"], request["clientRequestId"])
        self.assertNotEqual(runtime.files["allocation.py"], before)
        self.assertIn("return [0 for _ in weights]", runtime.files["allocation.py"])

    def test_summary_is_descriptive_only(self) -> None:
        records = [
            {
                "treatment": "exact-replacement-v1",
                "candidateCompleted": True,
                "visiblePassed": True,
                "hiddenPassed": True,
                "modelCalls": 4,
                "toolCalls": 5,
                "elapsedMs": 1000,
                "rejectedObservations": 0,
                "usage": {"totalTokens": 100},
            }
        ]
        summary = runner._summaries(records)["exact-replacement-v1"]
        self.assertEqual(summary["runs"], 1)
        self.assertEqual(summary["hiddenPassed"], 1)
        self.assertEqual(summary["meanTotalTokens"], 100)


if __name__ == "__main__":
    unittest.main()
