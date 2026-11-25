"""Native OPA bundle lifecycle experiment using only synthetic arithmetic.

The fixture is a disposable local bundle publisher, not a production service,
authorization evaluator, policy distributor, or deployment mechanism.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import http.server
import json
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

POLICY = """package demo
import rego.v1
result := {"revision": data.revision, "value": sum(input.numbers) + data.offset}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def bundle(opa: Path, root: Path, revision: str, offset: int) -> bytes:
    source = root / revision
    source.mkdir()
    (source / "demo.rego").write_text(POLICY, encoding="utf-8")
    (source / "data.json").write_text(
        json.dumps({"revision": revision, "offset": offset}), encoding="utf-8"
    )
    output = root / (revision + ".tar.gz")
    subprocess.run(
        [str(opa), "build", "-b", str(source), "-r", revision, "-o", str(output)],
        check=True,
        timeout=8,
        capture_output=True,
    )
    return output.read_bytes()


class Publisher:
    """In-memory synthetic fixture; no external network or credentials."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.body: bytes | None = None
        self.requests: dict[str, int] = {}

    def publish(self, body: bytes | None) -> str:
        identity = hashlib.sha256(body or b"").hexdigest()
        with self.lock:
            self.body = body
        return identity

    def count(self, identity: str) -> int:
        with self.lock:
            return self.requests.get(identity, 0)

    def capture(self) -> bytes | None:
        with self.lock:
            body = self.body
            identity = hashlib.sha256(body or b"").hexdigest()
            self.requests[identity] = self.requests.get(identity, 0) + 1
            return body


def qualify(opa: Path, root: Path) -> dict:
    fixture = Publisher()
    first = bundle(opa, root, "demo-a", 7)
    second = bundle(opa, root, "demo-b", 23)
    missing = fixture.publish(None)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = fixture.capture()
            if self.path != "/bundle.tar.gz" or body is None:
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:
            pass

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    observations: list[dict] = []
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as publisher:
        thread = threading.Thread(target=publisher.serve_forever, daemon=True)
        thread.start()
        config = root / "opa.json"
        config.write_text(
            json.dumps(
                {
                    "services": {"fixture": {"url": f"http://127.0.0.1:{publisher.server_port}"}},
                    "bundles": {
                        "fixture": {
                            "service": "fixture",
                            "resource": "bundle.tar.gz",
                            "polling": {"min_delay_seconds": 1, "max_delay_seconds": 1},
                            "persist": False,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"

        def start():
            return subprocess.Popen(
                [
                    str(opa),
                    "run",
                    "--server",
                    "--addr",
                    f"127.0.0.1:{port}",
                    "--config-file",
                    str(config),
                ],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        def stop(proc) -> None:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)

        def request(path, body=None):
            try:
                req = urllib.request.Request(
                    base + path,
                    data=None if body is None else json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with opener.open(req, timeout=1) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as exc:
                return exc.code, {}
            except OSError:
                return 0, {}

        def wait_for(predicate, label, timeout=15):
            begin = time.monotonic()
            while time.monotonic() - begin < timeout:
                if proc.poll() is not None:
                    raise RuntimeError(f"OPA exited during {label}")
                if predicate():
                    return round((time.monotonic() - begin) * 1000, 3)
                time.sleep(0.05)
            raise RuntimeError(f"native condition not observed: {label}")

        def query(numbers):
            return request("/v1/data/demo/result?metrics=true", {"input": {"numbers": numbers}})

        def matches(revision, value):
            status, response = query([1, 2, 3])
            return status == 200 and response.get("result") == {
                "revision": revision,
                "value": value,
            }

        def absent():
            status, response = query([1, 2, 3])
            return status != 200 or "result" not in response

        proc = start()
        try:
            wait_for(lambda: request("/health")[0] == 200, "server health")
            wait_for(lambda: fixture.count(missing) > 0, "missing initial bundle")
            require(
                request("/health?bundles=true")[0] != 200 and absent(),
                "unloaded instance unexpectedly ready with a result",
            )
            observations.append({"phase": "cold_missing", "qualified": False})

            fixture.publish(first)
            elapsed = wait_for(lambda: matches("demo-a", 13), "first activation")
            require(request("/health?bundles=true")[0] == 200, "bundle not ready")
            observations.append({"phase": "first_activation", "observedMs": elapsed})

            # One native request returns both synthetic identity and result.
            # Never infer per-request identity merely from an independent health read.
            def sample(i):
                status, response = query([i, 2])
                result = response.get("result")
                require(
                    status == 200 and result == {"revision": "demo-a", "value": i + 9},
                    "concurrent arithmetic mismatch",
                )
                return int(response.get("metrics", {}).get("counter_server_query_cache_hit", 0))

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                hits = list(pool.map(sample, range(32)))
            observations.append(
                {
                    "phase": "warm_concurrent",
                    "samples": len(hits),
                    "reportedPreparedQueryHits": sum(hits),
                }
            )

            invalid = fixture.publish(b"not a valid bundle")
            wait_for(lambda: fixture.count(invalid) >= 2, "invalid bundle downloads")
            require(matches("demo-a", 13), "old synthetic snapshot not retained")
            observations.append(
                {
                    "phase": "invalid_update",
                    "lastObservedRevision": "demo-a",
                    "bundleHealthStatus": request("/health?bundles=true")[0],
                }
            )

            fixture.publish(second)
            elapsed = wait_for(lambda: matches("demo-b", 29), "second activation")
            observations.append({"phase": "valid_recovery", "observedMs": elapsed})

            prior = fixture.count(missing)
            fixture.publish(None)
            wait_for(lambda: fixture.count(missing) >= prior + 2, "publisher unavailable")
            require(matches("demo-b", 29), "last active synthetic result disappeared")
            observations.append(
                {
                    "phase": "publisher_unavailable",
                    "lastObservedRevision": "demo-b",
                    "bundleHealthStatus": request("/health?bundles=true")[0],
                }
            )

            stop(proc)
            prior = fixture.count(missing)
            proc = start()
            wait_for(lambda: request("/health")[0] == 200, "restart health")
            wait_for(lambda: fixture.count(missing) > prior, "restart missing bundle")
            require(
                request("/health?bundles=true")[0] != 200 and absent(),
                "fresh non-persistent instance retained old result",
            )
            observations.append({"phase": "restart_without_bundle", "qualified": False})

            fixture.publish(second)
            elapsed = wait_for(lambda: matches("demo-b", 29), "restart recovery")
            observations.append({"phase": "restart_recovery", "observedMs": elapsed})
        finally:
            stop(proc)
            publisher.shutdown()
            thread.join(timeout=3)
    return {
        "standing": "SYNTHETIC_NATIVE_BUNDLE_LIFECYCLE_ONLY",
        "bundleSha256": {
            "demo-a": hashlib.sha256(first).hexdigest(),
            "demo-b": hashlib.sha256(second).hexdigest(),
        },
        "observations": observations,
        "boundary": "No real authorization, production readiness, or signed-bundle qualification.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opa", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="security-opa-bundle-") as root:
        print(json.dumps(qualify(args.opa.resolve(strict=True), Path(root)), indent=2))


if __name__ == "__main__":
    main()
