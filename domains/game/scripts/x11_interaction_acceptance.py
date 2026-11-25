"""Room exported-product consumer: private Xvfb, XTEST and window-local RGB."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from native_process import verify_process
from rendered_product_acceptance import PRODUCT_SIZES, digest, require

WIDTH, HEIGHT = PRODUCT_SIZES["room-encounter"]
STATUS_ROWS = (64, 128)  # source-bound Room view at the contracted resolution
FRAME_BYTES = WIDTH * HEIGHT * 3


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def status_strip(raw):
    return raw[STATUS_ROWS[0] * WIDTH * 3:STATUS_ROWS[1] * WIDTH * 3]


def verify_relations(frames):
    names = ("baseline", "baseline_repeat", "irrelevant", "attack",
             "restart", "attack_repeat", "restart_repeat")
    require(set(frames) == set(names), "wrong interaction inventory")
    require(all(len(v) == FRAME_BYTES for v in frames.values()), "wrong raster size")
    b, repeat, irrelevant, attack, reset, attack2, reset2 = (frames[n] for n in names)
    require(b == repeat == irrelevant, "idle or irrelevant key changed startup")
    require(status_strip(b) != status_strip(attack), "attack did not change status")
    require(status_strip(b) == status_strip(reset), "restart did not restore status")
    require(attack == attack2 and reset == reset2, "action/reset replay differs")
    return {name: {"rgb_sha256": sha(frames[name]),
                   "status_sha256": sha(status_strip(frames[name]))} for name in names}


class XTest:
    """Only the small native ABI needed by this isolated consumer."""

    def __init__(self):
        x, t = c.CDLL("libX11.so.6"), c.CDLL("libXtst.so.6")
        D, W, I, U = c.c_void_p, c.c_ulong, c.c_int, c.c_uint

        def bind(lib, name, result, *args):
            f = getattr(lib, name)
            f.restype, f.argtypes = result, args
            return f

        self.close = bind(x, "XCloseDisplay", I, D)
        self.root = bind(x, "XDefaultRootWindow", W, D)
        self.query = bind(x, "XQueryTree", I, D, W, c.POINTER(W), c.POINTER(W),
                          c.POINTER(c.POINTER(W)), c.POINTER(U))
        self.free = bind(x, "XFree", I, D)
        self.focus = bind(x, "XSetInputFocus", I, D, W, I, W)
        self.get_focus = bind(x, "XGetInputFocus", I, D, c.POINTER(W), c.POINTER(I))
        self.sync = bind(x, "XSync", I, D, I)
        self.sym = bind(x, "XStringToKeysym", W, c.c_char_p)
        self.key = bind(x, "XKeysymToKeycode", c.c_ubyte, D, W)
        self.fake = bind(t, "XTestFakeKeyEvent", I, D, U, I, W)
        self.geometry = bind(x, "XGetGeometry", I, D, W, c.POINTER(W),
                             c.POINTER(I), c.POINTER(I), c.POINTER(U), c.POINTER(U),
                             c.POINTER(U), c.POINTER(U))
        self.display = bind(x, "XOpenDisplay", D, c.c_char_p)(None)
        require(self.display, "private X11 display unavailable")

    def windows(self):
        root, parent, children, count = c.c_ulong(), c.c_ulong(), c.POINTER(c.c_ulong)(), c.c_uint()
        require(self.query(self.display, self.root(self.display), c.byref(root),
                           c.byref(parent), c.byref(children), c.byref(count)), "XQueryTree failed")
        try:
            require(count.value <= 128, "unexpected window inventory")
            return [children[i] for i in range(count.value)]
        finally:
            if children:
                self.free(children)

    def target(self, pid):
        hits = []
        for window in self.windows():
            p = subprocess.run(["xprop", "-id", str(window), "_NET_WM_PID", "WM_NAME"],
                               capture_output=True, text=True, timeout=3)
            if (p.returncode == 0 and
                    re.search(rf"^_NET_WM_PID\(CARDINAL\) = {pid}$", p.stdout, re.M) and
                    re.search(r'^WM_NAME\(STRING\) = "Room Encounter"$', p.stdout, re.M)):
                hits.append(window)
        require(len(hits) <= 1, "ambiguous target window")
        return hits[0] if hits else None

    def check_geometry(self, window):
        root, x, y = c.c_ulong(), c.c_int(), c.c_int()
        w, h, border, depth = c.c_uint(), c.c_uint(), c.c_uint(), c.c_uint()
        require(self.geometry(self.display, window, c.byref(root), c.byref(x), c.byref(y),
                              c.byref(w), c.byref(h), c.byref(border), c.byref(depth)),
                "target geometry unavailable")
        require((w.value, h.value) == (WIDTH, HEIGHT), "target geometry differs")

    def check_focus(self, window):
        actual, revert = c.c_ulong(), c.c_int()
        self.get_focus(self.display, c.byref(actual), c.byref(revert))
        require(actual.value == window, "target lost input focus")

    def press(self, window, name):
        self.check_focus(window)
        code = self.key(self.display, self.sym(name.encode("ascii")))
        require(code != 0, "unmapped key")
        require(self.fake(self.display, code, 1, 0), "key press failed")
        try:
            self.sync(self.display, 0)
            time.sleep(0.12)
        finally:
            require(self.fake(self.display, code, 0, 0), "key release failed")
            self.sync(self.display, 0)
        time.sleep(0.4)


def capture(x, window, pid):
    require(x.target(pid) == window, "target window identity changed")
    x.check_geometry(window)
    p = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-f", "x11grab", "-window_id", str(window),
         "-draw_mouse", "0", "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", "30",
         "-i", os.environ["DISPLAY"], "-frames:v", "1", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-threads", "1", "pipe:1"],
        capture_output=True, timeout=8)
    require(p.returncode == 0 and not p.stderr and len(p.stdout) == FRAME_BYTES,
            "window capture failed")
    return p.stdout


def isolated_child(executable, root):
    # Only entered by the outer launcher with its fresh private Xauthority file.
    require(os.environ.get("GAME_X11_PRIVATE_ROOT") == str(root) and
            os.environ.get("XAUTHORITY") == str(root / "authority") and
            (root / "authority").is_file() and
            re.fullmatch(r":\d+", os.environ.get("DISPLAY", "")), "not an isolated display")
    x = XTest()
    p = None
    try:
        p = subprocess.Popen([str(executable), "--resolution", f"{WIDTH}x{HEIGHT}",
                              "--position", "0,0", "--audio-driver", "Dummy",
                              "--max-fps", "30", "--quit-after", "900"],
                             cwd=executable.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        window = None
        for _ in range(50):
            require(p.poll() is None, "game exited before window")
            window = x.target(p.pid)
            if window is not None:
                break
            time.sleep(0.2)
        require(window is not None, "target window unavailable")
        x.check_geometry(window)
        x.focus(x.display, window, 2, 0)
        x.sync(x.display, 0)
        time.sleep(0.5)
        x.check_focus(window)
        frames = {"baseline": capture(x, window, p.pid),
                  "baseline_repeat": capture(x, window, p.pid)}
        for name, key in (("irrelevant", "F12"), ("attack", "a"), ("restart", "r"),
                          ("attack_repeat", "a"), ("restart_repeat", "r")):
            require(x.target(p.pid) == window, "target window identity changed")
            x.press(window, key)
            frames[name] = capture(x, window, p.pid)
        relations = verify_relations(frames)
        out, err = p.communicate(timeout=40)
        stdout, stderr = out.decode(errors="replace"), err.decode(errors="replace")
        verify_process(p.returncode, stdout, stderr)
        renderer = [s for s in stdout.splitlines() if "Using Device:" in s]
        require(len(renderer) == 1, "renderer witness missing")
        return {"frames": relations, "pid": p.pid, "window_id": window,
                "renderer": renderer[0], "keys": ["F12", "a", "r", "a", "r"]}
    finally:
        if p is not None and p.poll() is None:
            p.kill()
            p.wait()
        x.close(x.display)


def consume(executable, expected_sha):
    require(executable.is_absolute() and executable.is_file() and not executable.is_symlink(),
            "explicit absolute regular executable required")
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha) and digest(executable) == expected_sha,
            "input executable identity differs")
    for command in ("xvfb-run", "Xvfb", "xauth", "xprop", "ffmpeg"):
        require(shutil.which(command), f"missing {command}")
    with tempfile.TemporaryDirectory(prefix="game-x11-") as tmp:
        root = Path(tmp)
        env = os.environ.copy()
        env.pop("DISPLAY", None)
        env.pop("XAUTHORITY", None)
        env["GAME_X11_PRIVATE_ROOT"] = tmp
        for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            path = root / name
            path.mkdir()
            env[name] = str(path)
        args = ["xvfb-run", "-a", "-f", str(root / "authority"), "-s",
                "-screen 0 1280x800x24 -nolisten tcp", sys.executable,
                str(Path(__file__).resolve()), "--executable", str(executable),
                "--sha256", expected_sha, "--private-child", tmp]
        proc = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        try:
            out, err = proc.communicate(timeout=80)
        except BaseException:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
            raise
        require(proc.returncode == 0, f"private consumer rejected: {err[-3000:].decode(errors='replace')}")
        result = json.loads(out)
        require(digest(executable) == expected_sha, "executable identity changed")
        return {"status": "PASS", "scope": "isolated_linux_x11_synthetic_input_and_raster",
                "executable_sha256": expected_sha, "width": WIDTH, "height": HEIGHT,
                "status_rows": list(STATUS_ROWS), **result,
                "physical_keyboard": "NOT_EVALUATED", "physical_audio": "NOT_EVALUATED",
                "human_quality": "NOT_EVALUATED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--private-child", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.private_child:
            require(digest(args.executable) == args.sha256, "child identity differs")
            result = isolated_child(args.executable, args.private_child)
        else:
            result = consume(args.executable, args.sha256)
    except (ValueError, AssertionError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"X11 interaction rejected: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
