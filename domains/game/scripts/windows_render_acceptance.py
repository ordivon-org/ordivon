"""Cross-platform consumer of a Windows native capture; no desktop screenshot."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

from hosted_product_acceptance import verify_archive
from native_process import verify_process
from product_acceptance_contract import FRAMES, PRODUCT_SIZES, digest, require, verify_rasters


def bounded_text(path, limit=1024 * 1024):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit,
            "capture text missing or too large")
    return path.read_text(encoding="utf-8-sig", errors="strict")


def verify_capture_receipt(receipt, identity):
    require(isinstance(receipt, dict) and set(receipt) ==
            {"product", "executable_sha256", "pid", "session", "exit_code", "hwnd", "frames"},
            "native capture inventory differs")
    require(receipt["product"] == identity["product"] and
            receipt["executable_sha256"] == identity["executable_sha256"] and
            type(receipt["pid"]) is int and receipt["pid"] > 0 and
            type(receipt["session"]) is int and receipt["session"] == 1 and
            type(receipt["exit_code"]) is int and receipt["exit_code"] == 0 and
            type(receipt["hwnd"]) is int and receipt["hwnd"] >= 0,
            "native capture identity/session differs")
    frames = receipt["frames"]
    require(isinstance(frames, list) and len(frames) == FRAMES and
            all(isinstance(f, dict) and set(f) == {"name", "sha256"} and
                f["name"] == f"frame{i:08d}.png" and isinstance(f["sha256"], str) and
                re.fullmatch(r"[0-9a-f]{64}", f["sha256"])
                for i, f in enumerate(frames)), "native capture frame inventory differs")


def qualify_capture(root, identity):
    product = identity["product"]
    sha = identity["executable_sha256"]
    executable = root / f"{product}.exe"
    require(executable.is_file() and not executable.is_symlink() and
            digest(executable) == sha, "Windows executable identity differs")
    out = root / f"{product}-capture"
    require(out.is_dir() and not out.is_symlink() and not (out / "frames").is_symlink(),
            "invalid capture directory")
    receipt = json.loads(bounded_text(out / "capture.json"))
    verify_capture_receipt(receipt, identity)
    log = bounded_text(out / "native.log")
    stdout = bounded_text(out / "stdout.txt")
    stderr = bounded_text(out / "stderr.txt")
    verify_process(receipt["exit_code"], log + "\n" + stdout, stderr)
    renderer = [s for s in log.splitlines() if "Using Device:" in s]
    require(len(renderer) == 1 and "Movie Maker mode enabled" in log,
            "native renderer/movie witness missing")
    frames = verify_rasters(out / "frames", *PRODUCT_SIZES[product])
    expected = [{"name": f"frame{i:08d}.png", "sha256": f["png_sha256"]}
                for i, f in enumerate(frames)]
    require(receipt["frames"] == expected, "Windows and decoder frame identities differ")
    require(digest(root / f"{product}.exe") == sha, "Windows executable changed")
    return {"status": "PASS", "scope": "windows_native_session1_rendered_startup",
            **identity, "pid": receipt["pid"], "session": receipt["session"],
            "hwnd_observed": receipt["hwnd"], "renderer": renderer[0], "frames": frames,
            "physical_display": "NOT_EVALUATED", "physical_input": "NOT_EVALUATED",
            "physical_audio": "NOT_EVALUATED", "human_quality": "NOT_EVALUATED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "verify"))
    p.add_argument("--stage", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--product", choices=PRODUCT_SIZES, required=True)
    args = p.parse_args()
    try:
        require(args.stage.is_absolute() and args.stage.is_dir() and not args.stage.is_symlink(),
                "invalid stage")
        # Re-derive exact identity from the immutable archive for both operations;
        # never trust a sidecar as executable identity authority.
        if args.action == "prepare":
            _, result = verify_archive(args.archive, args.sha256, args.source,
                                       args.product, args.stage, platform="windows")
        else:
            import tempfile
            with tempfile.TemporaryDirectory(prefix="game-win-identity-") as tmp:
                _, identity = verify_archive(args.archive, args.sha256, args.source,
                                             args.product, Path(tmp), platform="windows")
            result = qualify_capture(args.stage, identity)
    except (ValueError, AssertionError, OSError, zipfile.BadZipFile, tarfile.TarError,
            subprocess.SubprocessError) as exc:
        p.exit(1, f"Windows render rejected: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
