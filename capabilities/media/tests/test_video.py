from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.video import BT709_H264_METADATA, normalize_h264_bt709


class VideoTransformTests(unittest.TestCase):
    def test_bt709_normalization_uses_stream_copy_and_replaces_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "video.mp4"
            path.write_bytes(b"before")

            def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                self.assertIn("copy", args)
                self.assertIn(BT709_H264_METADATA, args)
                self.assertNotIn("libx264", args)
                Path(args[-1]).write_bytes(b"after")
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

            with patch("ordivon_studio.video.subprocess.run", side_effect=fake_run):
                normalize_h264_bt709(path)

            self.assertEqual(path.read_bytes(), b"after")
            self.assertEqual(list(Path(directory).glob(".*.bt709-*.mp4")), [])

    def test_bt709_normalization_preserves_original_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "video.mp4"
            path.write_bytes(b"original")
            failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="bad filter")
            with patch("ordivon_studio.video.subprocess.run", return_value=failed):
                with self.assertRaisesRegex(RuntimeError, "bad filter"):
                    normalize_h264_bt709(path)
            self.assertEqual(path.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
