"""Execute the actual owner task in a disposable native test fixture."""

from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

OWNER = Path(__file__).resolve().parents[1]


class PropertyTaskQualificationTests(unittest.TestCase):
    def test_caller_selection_and_plugins_cannot_suppress_required_execution(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            owner = root / "packages/data"
            properties = owner / "tests/properties"
            study = root / "studies/data-lifecycle/tests"
            properties.mkdir(parents=True)
            study.mkdir(parents=True)
            shutil.copyfile(OWNER / "mise.toml", owner / "mise.toml")

            # These markers are observations of executed test bodies, not
            # interpretations of pytest's collection count or summary.
            (properties / "test_required.py").write_text(
                "import os\n"
                "from pathlib import Path\n"
                "def test_keep():\n"
                "    pass\n"
                "def test_sentinel():\n"
                "    Path(__file__).with_name('executed').touch()\n"
                "    assert os.environ['ORDIVON_TEST_SENTINEL_FAIL'] == '0', "
                "'required sentinel executed'\n",
                encoding="utf-8",
            )
            (study / "test_generated.py").write_text(
                "from pathlib import Path\n"
                "from hypothesis import given, settings, strategies as st\n"
                "@settings(max_examples=5, database=None, derandomize=True)\n"
                "@given(st.integers())\n"
                "def test_generated(n):\n"
                "    Path(__file__).with_name('executed').touch()\n",
                encoding="utf-8",
            )
            markers = [properties / "executed", study / "executed"]
            env = os.environ.copy()
            for key in (
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
            ):
                env.pop(key, None)
            # Resolve the real tool in the source owner before leaving the
            # repository's mise configuration. CI may expose only a shim.
            uv = Path(
                subprocess.check_output(
                    ["mise", "which", "uv"], cwd=OWNER, text=True
                ).strip()
            )
            self.assertTrue(uv.is_file() and uv.is_absolute(), uv)
            env["PATH"] = str(uv.parent) + os.pathsep + env["PATH"]
            # Trust only the disposable copy for this subprocess.
            env["MISE_TRUSTED_CONFIG_PATHS"] = str(root)
            for name, options, expected in (
                ("healthy", {"ORDIVON_TEST_SENTINEL_FAIL": "0"}, 0),
                (
                    "contaminated",
                    {
                        "ORDIVON_TEST_SENTINEL_FAIL": "1",
                        "PYTEST_ADDOPTS": "--collect-only -k keep",
                        "PYTEST_PLUGINS": "nonexistent_test_plugin",
                        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                    },
                    1,
                ),
            ):
                with self.subTest(name=name):
                    for marker in markers:
                        marker.unlink(missing_ok=True)
                    result = subprocess.run(
                        ["mise", "run", "test:properties"],
                        cwd=owner,
                        check=False,
                        env=env | options,
                        capture_output=True,
                        text=True,
                        timeout=90,
                    )
                    diagnostics = result.stdout + result.stderr
                    self.assertEqual(result.returncode, expected, diagnostics)
                    self.assertTrue(
                        all(marker.is_file() for marker in markers), diagnostics
                    )
                    if expected:
                        self.assertIn("required sentinel executed", diagnostics)
