"""Synthetic package-data fixtures, independent of service behavior."""

import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile

from qualify_authzen_wheel import PACKAGE, check_package_sources


class WheelSourceQualificationTests(unittest.TestCase):
    def test_exact_source_inventory_and_bytes(self):
        expected = {PACKAGE + "sample.txt": b"sample document"}
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "fixture.whl"
            cases = [
                (expected, None),
                ({}, "inventory mismatch"),
                ({**expected, PACKAGE + "extra.txt": b"extra"}, "inventory mismatch"),
                ({PACKAGE + "sample.txt": b"other document"}, "bytes mismatch"),
            ]
            for files, error in cases:
                with self.subTest(error=error):
                    with ZipFile(archive, "w") as output:
                        for name, data in files.items():
                            output.writestr(name, data)
                        output.writestr("fixture.dist-info/METADATA", "Name: fixture")
                    if error is None:
                        self.assertEqual(check_package_sources(archive, expected), 1)
                    else:
                        with self.assertRaisesRegex(ValueError, error):
                            check_package_sources(archive, expected)

    def test_duplicate_member_is_not_a_unique_inventory(self):
        name = PACKAGE + "sample.txt"
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "fixture.whl"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with ZipFile(archive, "w") as output:
                    output.writestr(name, b"one")
                    output.writestr(name, b"two")
            with self.assertRaisesRegex(ValueError, "duplicate archive member"):
                check_package_sources(archive, {name: b"two"})
