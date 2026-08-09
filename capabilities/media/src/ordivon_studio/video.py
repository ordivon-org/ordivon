from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


BT709_H264_METADATA = (
    "h264_metadata="
    "video_full_range_flag=0:"
    "colour_primaries=1:"
    "transfer_characteristics=1:"
    "matrix_coefficients=1"
)


def normalize_h264_bt709(path: Path, ffmpeg: str = "/usr/bin/ffmpeg") -> None:
    """Write complete BT.709 VUI signalling without re-encoding H.264 picture data."""
    if not path.is_file():
        raise FileNotFoundError(path)
    path = path.resolve()
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{path.stem}.bt709-",
        suffix=path.suffix or ".mp4",
        dir=path.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-y",
                "-i",
                str(path),
                "-map",
                "0",
                "-c",
                "copy",
                "-bsf:v",
                BT709_H264_METADATA,
                str(temporary),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"ffmpeg exited {result.returncode}")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError("ffmpeg produced no normalized video")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
