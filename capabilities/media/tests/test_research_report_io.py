from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.research.report_io import write_report_json

ROOT = Path(__file__).resolve().parents[1]


class ResearchReportIOTest(unittest.TestCase):
    def test_all_three_cli_writers_have_one_implementation(self) -> None:
        for name in (
            "run-r5-grounded-meaning.py",
            "run-r6-creative-alpha.py",
            "run-r6-creative-validity.py",
        ):
            with self.subTest(name=name):
                script = runpy.run_path(str(ROOT / "scripts" / name))
                self.assertIs(script["write_report_json"], write_report_json)

    def test_preserves_nested_directory_utf8_sort_newline_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested" / "report.json"
            write_report_json(str(path), {"汉字": [1, False, None, "é"], "a": -0.0})
            self.assertEqual(
                path.read_bytes(),
                b'{\n  "a": -0.0,\n  "\xe6\xb1\x89\xe5\xad\x97": [\n    1,\n    false,\n    null,\n    "\xc3\xa9"\n  ]\n}\n',
            )
            write_report_json(path, {"x": float("nan")})
            self.assertEqual(path.read_bytes(), b'{\n  "x": NaN\n}\n')
