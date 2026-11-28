"""Platform-neutral product identity and rendered raster acceptance contract."""
import hashlib
import struct
import subprocess

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
