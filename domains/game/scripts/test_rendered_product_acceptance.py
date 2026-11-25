"""Real FFmpeg decoder contract, not a second game renderer."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from rendered_product_acceptance import FRAMES, verify_rasters


class RasterContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, source in (("varied", "testsrc=size=16x16:rate=1"),
                             ("flat", "color=black:size=16x16:rate=1")):
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi",
                            "-i", source, "-frames:v", "1", "-threads", "1",
                            str(self.root / f"{name}.fixture.png")],
                           check=True, capture_output=True)
        self.frames = self.root / "frames"
        self.frames.mkdir()
        for i in range(FRAMES):
            shutil.copyfile(self.root / "varied.fixture.png", self.frames / f"frame{i:08d}.png")

    def test_real_decode(self):
        result = verify_rasters(self.frames, 16, 16)
        self.assertEqual(len(result), FRAMES)
        self.assertTrue(all(frame["nonuniform"] for frame in result))

    def test_missing_frame(self):
        (self.frames / "frame00000007.png").unlink()
        with self.assertRaisesRegex(ValueError, "inventory"):
            verify_rasters(self.frames, 16, 16)

    def test_extra_frame(self):
        shutil.copyfile(self.root / "varied.fixture.png", self.frames / "frame00000008.png")
        with self.assertRaisesRegex(ValueError, "inventory"):
            verify_rasters(self.frames, 16, 16)

    def test_wrong_size(self):
        with self.assertRaisesRegex(ValueError, "dimensions"):
            verify_rasters(self.frames, 17, 16)

    def test_truncated_frame(self):
        p = self.frames / "frame00000007.png"
        p.write_bytes(p.read_bytes()[:24])
        with self.assertRaisesRegex(ValueError, "decode|byte count"):
            verify_rasters(self.frames, 16, 16)

    def test_uniform_final(self):
        shutil.copyfile(self.root / "flat.fixture.png", self.frames / "frame00000007.png")
        with self.assertRaisesRegex(ValueError, "uniform final"):
            verify_rasters(self.frames, 16, 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
