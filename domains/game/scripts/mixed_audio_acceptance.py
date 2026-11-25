"""Actual exported Room mixed audio, not speaker or microphone measurement."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time

from native_process import verify_process
from rendered_product_acceptance import digest, require
from x11_interaction_acceptance import (
    WIDTH, HEIGHT, XTest, require_private_display, run_private, status_strip,
)

FRAMES = 180
FPS = 30
RATE = 48000
CHANNELS = 2
PCM_BYTES = FRAMES * RATE // FPS * CHANNELS * 2


def summarize_pcm(raw):
    require(len(raw) == PCM_BYTES, "wrong PCM byte count")
    peak = nonzero = first = last = 0
    for index, (sample,) in enumerate(struct.iter_unpack("<h", raw)):
        if sample:
            if not nonzero:
                first = index // CHANNELS
            last = index // CHANNELS
            nonzero += 1
            peak = max(peak, abs(sample))
    return {"pcm_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "peak_s16": peak, "nonzero_samples": nonzero,
            "first_nonzero_frame": first if nonzero else None,
            "last_nonzero_frame": last if nonzero else None}


def verify_audio_relations(control, attack, reset):
    require(control["nonzero_samples"] == 0, "irrelevant input audible")
    require(attack["peak_s16"] > 100 and attack["nonzero_samples"] > 100,
            "attack mixed PCM silent or trivial")
    require(reset["nonzero_samples"] == 0, "reset input audible")


def decode_audio(path):
    require(path.is_file() and not path.is_symlink() and 44 <= path.stat().st_size <= 4 * 1024 * 1024,
            "WAV inventory/size invalid")
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                           "stream=codec_name,sample_rate,channels,duration",
                           "-of", "json", str(path)], capture_output=True, timeout=10, check=True)
    streams = json.loads(info.stdout)["streams"]
    require(len(streams) == 1 and streams[0].get("codec_name") == "pcm_s32le" and
            streams[0].get("sample_rate") == str(RATE) and streams[0].get("channels") == CHANNELS,
            "unexpected native WAV format")
    require(abs(float(streams[0]["duration"]) - FRAMES / FPS) < 0.00001, "unexpected audio duration")
    proc = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(path),
                           "-map", "0:a:0", "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1"],
                          capture_output=True, timeout=20)
    require(proc.returncode == 0 and not proc.stderr, "FFmpeg audio decode failed")
    return {"wav_sha256": digest(path), "source_codec": "pcm_s32le", **summarize_pcm(proc.stdout)}


def decode_frame(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 8 * 1024 * 1024,
            "invalid synchronized frame")
    proc = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror",
                           "-threads", "1", "-i", str(path), "-frames:v", "1",
                           "-pix_fmt", "rgb24", "-f", "rawvideo", "-threads", "1", "pipe:1"],
                          capture_output=True, timeout=10)
    require(proc.returncode == 0 and not proc.stderr and
            len(proc.stdout) == WIDTH * HEIGHT * 3, "synchronized frame decode failed")
    return proc.stdout


def record(x, executable, root, key):
    root.mkdir()
    env = os.environ.copy()
    for var in ("XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME"):
        path = root / var
        path.mkdir()
        env[var] = str(path)
    p = subprocess.Popen([str(executable), "--resolution", f"{WIDTH}x{HEIGHT}", "--position", "0,0",
                          "--audio-driver", "Dummy", "--write-movie", str(root / "frame.png"),
                          "--fixed-fps", str(FPS), "--quit-after", str(FRAMES)],
                         cwd=executable.parent, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        window = None
        for _ in range(80):
            require(p.poll() is None, "game exited before target")
            window = x.target(p.pid, movie=True)
            if window is not None:
                break
            time.sleep(0.05)
        require(window is not None, "target window unavailable")
        x.check_geometry(window)
        x.focus(x.display, window, 2, 0)
        x.sync(x.display, 0)
        time.sleep(0.25)
        # Observe a completed pre-input movie frame, then send exactly one key.
        # Decode both source-bound frames after the writer exits; no second
        # x11grab path competing with the native movie capture.
        for _ in range(60):
            at = len(list(root.glob("frame*.png")))
            if at >= 4:
                break
            require(p.poll() is None, "game exited before input")
            time.sleep(0.05)
        require(4 <= at < FRAMES - 30, "event outside bounded recording")
        require(x.target(p.pid, movie=True) == window, "target identity changed before input")
        x.press(window, key)
        end = len(list(root.glob("frame*.png")))
        require(at + 2 < end < FRAMES, "recording ended during event")
        out, err = p.communicate(timeout=45)
        stdout = out.decode(errors="replace")
        verify_process(p.returncode, stdout, err.decode(errors="replace"))
        renderer = [line for line in stdout.splitlines() if "Using Device:" in line]
        require(len(renderer) == 1 and "Movie Maker mode enabled" in stdout and
                f"{FRAMES} frames at {FPS} FPS" in stdout, "native movie witness missing")
        require({f.name for f in root.glob("*.png")} ==
                {f"frame{i:08d}.png" for i in range(FRAMES)}, "wrong movie inventory")
        before = decode_frame(root / f"frame{at - 2:08d}.png")
        after = decode_frame(root / f"frame{end - 2:08d}.png")
        changed = status_strip(before) != status_strip(after)
        require(changed == (key == "a"), f"{key}: input/status relation failed")
        result = decode_audio(root / "frame.wav")
        return {"key": key, "pre_status_sha256": hashlib.sha256(status_strip(before)).hexdigest(),
                "post_status_sha256": hashlib.sha256(status_strip(after)).hexdigest(), "frame_count_before_input": at, "frame_count_after_input": end,
                "status_changed": changed, "pid": p.pid, "window_id": window,
                "renderer": renderer[0], **result}
    finally:
        if p.poll() is None:
            p.kill()
            p.wait()


def isolated_child(executable, root):
    require_private_display(root)
    x = XTest()
    try:
        results = {name: record(x, executable, root / name, key)
                   for name, key in (("control", "F12"), ("attack", "a"), ("reset", "r"))}
        verify_audio_relations(results["control"], results["attack"], results["reset"])
        return {"recordings": results}
    finally:
        x.close(x.display)


def consume(executable, expected_sha):
    result = run_private(executable, expected_sha, Path(__file__), timeout=140)
    return {"status": "PASS", "scope": "native_movie_maker_mixed_pcm_only",
            "executable_sha256": expected_sha, "sample_rate": RATE, "channels": CHANNELS,
            "fixed_fps": FPS, "frames_per_recording": FRAMES,
            "physical_audio": "NOT_EVALUATED", "human_quality": "NOT_EVALUATED", **result}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--executable", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--private-child", type=Path, help=argparse.SUPPRESS)
    args = p.parse_args()
    try:
        if args.private_child:
            require(digest(args.executable) == args.sha256, "child identity differs")
            result = isolated_child(args.executable, args.private_child)
        else:
            result = consume(args.executable, args.sha256)
    except (ValueError, AssertionError, OSError, subprocess.SubprocessError) as exc:
        p.exit(1, f"mixed audio rejected: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
