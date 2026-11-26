"""Observe actual exported study build; reuse private X11 consumer primitives."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from native_process import verify_process
from x11_interaction_acceptance import (WIDTH, HEIGHT, XTest, capture, digest,
    require, require_private_display, run_private, sha, status_strip)


def observe(executable, root):
    require_private_display(root)
    x = XTest()
    p = None
    try:
        p = subprocess.Popen([str(executable), "--resolution", f"{WIDTH}x{HEIGHT}",
                              "--position", "0,0", "--audio-driver", "Dummy",
                              "--max-fps", "30", "--quit-after", "600"],
                             cwd=executable.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        window = None
        for _ in range(50):
            require(p.poll() is None, "early native exit")
            window = x.target(p.pid)
            if window is not None:
                break
            time.sleep(0.2)
        require(window is not None, "missing study window")
        x.check_geometry(window)
        x.focus(x.display, window, 2, 0)
        x.sync(x.display, 0)
        time.sleep(0.5)
        frames = {"classic": capture(x, window, p.pid)}
        keys = (("trial", "t"), ("guard", "g"), ("save", "s"),
                ("guard2", "g"), ("load", "l"), ("restart", "r"))
        for name, key in keys:
            require(x.target(p.pid) == window, "window identity changed")
            x.press(window, key)
            frames[name] = capture(x, window, p.pid)
        status = {name: status_strip(raw) for name, raw in frames.items()}
        require(status["classic"] != status["trial"] != status["guard"] and
                status["guard"] != status["guard2"], "trial/guard status absent")
        require(status["save"] == status["guard"] == status["load"] and
                status["restart"] == status["trial"], "save/load/restart projection differs")
        saves = list((root / "XDG_DATA_HOME").rglob("room_encounter_run.cfg"))
        require(len(saves) == 1 and saves[0].is_file() and not saves[0].is_symlink()
                and 0 < saves[0].stat().st_size <= 16384, "save inventory")
        text = saves[0].read_text()
        relative = saves[0].relative_to(root / "XDG_DATA_HOME").as_posix()
        out, err = p.communicate(timeout=35)
        stdout = out.decode(errors="replace")
        verify_process(p.returncode, stdout, err.decode(errors="replace"))
        renderer = [s for s in stdout.splitlines() if "Using Device:" in s]
        require(len(renderer) == 1, "renderer missing")
        return {"frames": {k: sha(v) for k,v in status.items()},
                "keys": [key for _,key in keys], "save_path": relative,
                "save_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "save_text": text, "renderer": renderer[0], "pid": p.pid, "window": window}
    finally:
        if p is not None and p.poll() is None:
            p.kill()
            p.wait()
        x.close(x.display)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--executable", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--private-child", type=Path)
    a = p.parse_args()
    require(digest(a.executable) == a.sha256, "executable changed")
    result = observe(a.executable, a.private_child) if a.private_child else run_private(
        a.executable, a.sha256, Path(__file__), timeout=65)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
