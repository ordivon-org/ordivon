from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

MEDIA = Path(__file__).resolve().parents[2]
MEDIA_V2 = MEDIA / "media-v2"


class MediaV2OwnerToolResolutionTests(unittest.TestCase):
    def test_probe_and_smoke_scripts_resolve_media_owner_from_any_cwd(self) -> None:
        for relative in (
            "bin/probe-otio.sh",
            "bin/probe-timed-text.sh",
            "tests/otio-smoke.sh",
            "tests/timedtext-smoke.sh",
        ):
            path = MEDIA_V2 / relative
            line = next(
                (item for item in path.read_text().splitlines() if item.startswith("root=")),
                None,
            )
            self.assertIsNotNone(line, relative)
            with self.subTest(script=relative), tempfile.TemporaryDirectory() as temp:
                proc = subprocess.run(
                    [
                        "/usr/bin/bash",
                        "-c",
                        "set -euo pipefail\n" + line + '\nprintf "%s" "$root"',
                        str(path),
                    ],
                    cwd=temp,
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, str(MEDIA))

    def test_tool_wrappers_use_media_owner_uv_not_host_uv(self) -> None:
        for relative in ("bin/otiotool-pinned.sh", "bin/ttconv-pinned.sh"):
            path = MEDIA_V2 / relative
            data = path.read_text()
            line = next(
                (item for item in data.splitlines() if item.startswith("owner=")),
                None,
            )
            self.assertIsNotNone(line, relative)
            with self.subTest(script=relative), tempfile.TemporaryDirectory() as temp:
                proc = subprocess.run(
                    [
                        "/usr/bin/bash",
                        "-c",
                        "set -euo pipefail\n" + line + '\nprintf "%s" "$owner"',
                        str(path),
                    ],
                    cwd=temp,
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, str(MEDIA))
                self.assertIn('exec /usr/bin/mise -C "$owner" exec -- uv tool run ', data)
                self.assertNotIn("/usr/bin/uv", data)

    def test_smoke_fixtures_use_owner_uv_without_project_discovery(self) -> None:
        for relative in ("tests/otio-smoke.sh", "tests/timedtext-smoke.sh"):
            source = (MEDIA_V2 / relative).read_text()
            with self.subTest(script=relative):
                self.assertNotIn("/usr/bin/uv", source)
                if relative == "tests/otio-smoke.sh":
                    self.assertIn('/usr/bin/mise -C "$root" exec -- uv run --no-project ', source)
                else:
                    self.assertIn('ttconv="$root/media-v2/bin/ttconv-pinned.sh"', source)
                    self.assertIn('"$ttconv" convert ', source)


if __name__ == "__main__":
    unittest.main()
