"""Independent Linux rendered-startup consumer of an exact exported game."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from native_process import private_player_environment, verify_process

FRAMES = 8
FPS = 30
MAX_FRAME_BYTES = 8 * 1024 * 1024
PRODUCT_SIZES = {"beacon-relay": (480, 720), "room-encounter": (1152, 648)}
PNG = b"\x89PNG\r\n\x1a\n"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def verify_rasters(directory, width, height):
    require(0 < width <= 1920 and 0 < height <= 1080, "resolution outside contract")
    paths = [directory / f"frame{i:08d}.png" for i in range(FRAMES)]
    require(set(directory.glob("*.png")) == set(paths), "wrong frame inventory")
    for p in paths:
        require(p.is_file() and not p.is_symlink(), "not a regular frame")
        require(24 <= p.stat().st_size <= MAX_FRAME_BYTES, "frame size outside contract")
        with p.open("rb") as stream:
            head = stream.read(24)
        require(head[:16] == PNG + b"\x00\x00\x00\x0dIHDR", "invalid PNG header")
        require(struct.unpack(">II", head[16:24]) == (width, height), "frame dimensions differ")
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-threads", "1",
         "-f", "image2", "-start_number", "0", "-i", str(directory / "frame%08d.png"),
         "-frames:v", str(FRAMES), "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-threads", "1", "pipe:1"], capture_output=True, timeout=60, check=False)
    require(proc.returncode == 0 and not proc.stderr, "FFmpeg decode rejected frames")
    stride = width * height * 3
    require(len(proc.stdout) == FRAMES * stride, "decoded raster byte count differs")
    frames = []
    for i, path in enumerate(paths):
        raw = proc.stdout[i * stride:(i + 1) * stride]
        uniform = raw == raw[:3] * (width * height)
        frames.append({"index": i, "png_sha256": digest(path),
                       "rgb_sha256": hashlib.sha256(raw).hexdigest(),
                       "nonuniform": not uniform})
    require(frames[-1]["nonuniform"], "uniform final raster")
    return frames


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
        env = private_player_environment(directory)
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
