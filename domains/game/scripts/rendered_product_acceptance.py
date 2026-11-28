"""Independent Linux rendered-startup consumer of an exact exported game."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from native_process import verify_process

from product_acceptance_contract import FPS, FRAMES, PRODUCT_SIZES, digest, require, verify_rasters


def consume(executable, expected_sha, product):
    require(executable.is_absolute() and executable.is_file() and not executable.is_symlink(),
            "explicit absolute regular executable required")
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha) is not None, "invalid expected SHA")
    require(digest(executable) == expected_sha, "input executable identity differs")
    for command in ("xvfb-run", "ffmpeg"):
        require(shutil.which(command) is not None, f"missing {command}")
    width, height = PRODUCT_SIZES[product]
    with tempfile.TemporaryDirectory(prefix="game-rendered-") as tmp:
        directory = Path(tmp)
        output = directory / "frames"
        output.mkdir()
        # Do not read/write the normal player's app data.
        env = os.environ.copy()
        for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            path = directory / name
            path.mkdir()
            env[name] = str(path)
        proc = subprocess.run(
            ["xvfb-run", "-a", str(executable), "--rendering-method", "gl_compatibility",
             "--audio-driver", "Dummy", "--resolution", f"{width}x{height}",
             "--write-movie", str(output / "frame.png"), "--fixed-fps", str(FPS),
             "--quit-after", str(FRAMES)],
            cwd=executable.parent, env=env, capture_output=True, text=True,
            errors="replace", timeout=120, check=False)
        verify_process(proc.returncode, proc.stdout, proc.stderr)
        renderer = [line for line in proc.stdout.splitlines() if "Using Device:" in line]
        require(len(renderer) == 1 and "Movie Maker mode enabled" in proc.stdout,
                "actual renderer/movie witness missing")
        frames = verify_rasters(output, width, height)
        require(digest(executable) == expected_sha, "executable identity changed")
        ffmpeg = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True,
                                timeout=10, check=True).stdout.splitlines()[0]
        return {"status": "PASS", "scope": "linux_display_backed_rendered_startup_only",
                "product": product, "executable_sha256": expected_sha,
                "width": width, "height": height, "fixed_fps": FPS, "frames": frames,
                "renderer": renderer[0], "ffmpeg": ffmpeg,
                "physical_input": "NOT_EVALUATED", "physical_audio": "NOT_EVALUATED",
                "human_quality": "NOT_EVALUATED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--product", choices=PRODUCT_SIZES, required=True)
    args = parser.parse_args()
    try:
        result = consume(args.executable, args.sha256, args.product)
    except (ValueError, AssertionError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"rendered product rejected: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
