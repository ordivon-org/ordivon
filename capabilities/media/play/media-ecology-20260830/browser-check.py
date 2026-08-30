from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
_browser = os.environ.get("ORDIVON_CHROMIUM") or shutil.which("chromium") or shutil.which("chromium-browser")
CHROMIUM = Path(_browser) if _browser else None


def _command(width: int, height: int) -> list[str]:
    return [
        str(CHROMIUM),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
    ]


def run(width: int, height: int, name: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"media-ecology-{name}-") as temporary:
        screenshot = Path(temporary) / f"{name}.png"
        screenshot_run = subprocess.run(
            _command(width, height)
            + [f"--screenshot={screenshot}", (HERE / "index.html").as_uri()],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if screenshot_run.returncode != 0 or not screenshot.is_file() or screenshot.stat().st_size == 0:
            raise RuntimeError(
                f"Chromium screenshot failed for {name}: rc={screenshot_run.returncode} "
                f"stderr={screenshot_run.stderr}"
            )
        screenshot_bytes = screenshot.read_bytes()

        dom_run = subprocess.run(
            _command(width, height) + ["--dump-dom", (HERE / "index.html").as_uri()],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if dom_run.returncode != 0:
            raise RuntimeError(
                f"Chromium DOM check failed for {name}: rc={dom_run.returncode} "
                f"stderr={dom_run.stderr}"
            )
        dom = dom_run.stdout
        required = [
            'data-overflow-x="false"',
            'data-activity-cards="2"',
            'data-collection-works="5"',
            "Activity without a second truth system.",
        ]
        missing = [marker for marker in required if marker not in dom]
        if missing:
            raise RuntimeError(f"Chromium DOM acceptance failed for {name}; missing {missing}")

        return {
            "name": name,
            "viewport": [width, height],
            "horizontalOverflow": False,
            "activityCards": 2,
            "collectionWorks": 5,
            "screenshotBytes": len(screenshot_bytes),
            "screenshotDigest": "sha256:" + sha256(screenshot_bytes).hexdigest(),
        }


def main() -> None:
    if CHROMIUM is None or not CHROMIUM.is_file():
        raise RuntimeError("Workstation-managed Playwright Chromium is unavailable")
    checks = [run(1440, 1000, "desktop"), run(390, 844, "mobile")]
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.media-ecology-browser-acceptance",
        "browserExecutable": "<workstation-managed-browser>",
        "browserRole": "Workstation-managed physical equipment binding; not Media truth authority",
        "checks": checks,
    }
    (HERE / "browser-acceptance.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    sys.exit(main())
