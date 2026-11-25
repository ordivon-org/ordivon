"""Real FFmpeg decoder contract, not a second game renderer."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from native_process import verify_process
from rendered_product_acceptance import FRAMES, consume, digest, verify_rasters


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
                           check=True, capture_output=True, timeout=15)
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


class NativeBlankContract(unittest.TestCase):
    def test_actual_exported_blank(self):
        """A genuine native exit-zero is insufficient to qualify rendered startup."""
        with tempfile.TemporaryDirectory(prefix="game-native-blank-") as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "project.godot").write_text(
                'config_version=5\n[application]\nconfig/name="Blank counterexample"\n'
                'run/main_scene="res://blank.tscn"\n[display]\n'
                'window/size/viewport_width=480\nwindow/size/viewport_height=720\n'
                'window/size/window_width_override=480\nwindow/size/window_height_override=720\n'
                '[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
            (project / "blank.tscn").write_text(
                '[gd_scene format=3]\n\n[node name="BlankCounterexample" type="Node2D"]\n')
            game = Path(__file__).resolve().parents[1]
            shutil.copyfile(game / "examples/beacon-relay/export_presets.cfg",
                            project / "export_presets.cfg")
            exe = root / "blank.x86_64"
            for args in (["godot", "--headless", "--path", str(project), "--editor", "--import"],
                         ["godot", "--headless", "--path", str(project), "--export-release",
                          "Linux x86_64", str(exe)]):
                proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
                verify_process(proc.returncode, proc.stdout, proc.stderr)
            exe.chmod(0o700)
            proc = subprocess.run([str(exe), "--headless", "--quit-after", "8"],
                                  capture_output=True, text=True, timeout=30)
            verify_process(proc.returncode, proc.stdout, proc.stderr)
            with self.assertRaisesRegex(ValueError, "uniform final raster"):
                consume(exe, digest(exe), "beacon-relay")
            with self.assertRaisesRegex(ValueError, "input executable identity differs"):
                consume(exe, "0" * 64, "beacon-relay")


if __name__ == "__main__":
    unittest.main(verbosity=2)
