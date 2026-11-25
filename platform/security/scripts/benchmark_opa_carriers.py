"""Compare native OPA process carriers on non-authorizing synthetic arithmetic.

Only a disposable loopback instance and generated data are used. This is not
an authorization-policy benchmark, installed-service test, or deployment tool.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import socket
import statistics
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


def percentile95(samples: list[float]) -> float:
    return sorted(samples)[math.ceil(len(samples) * 0.95) - 1]


def benchmark(opa: Path, count: int) -> list[dict]:
    rng = random.Random(20261126)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    observations = []
    with tempfile.TemporaryDirectory(prefix="security-opa-carrier-") as root:
        p = Path(root)
        policy = p / "demo.rego"
        data = p / "data.json"
        policy.write_text(
            "package demo\nimport rego.v1\nresult := sum(input.numbers) + data.offset\n",
            encoding="utf-8",
        )
        data.write_text('{"offset":7}', encoding="utf-8")
        subprocess.run([str(opa), "check", "--strict", str(policy)], check=True)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        proc = subprocess.Popen(
            [str(opa), "run", "--server", "--addr", f"127.0.0.1:{port}",
             str(policy), str(data)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError("isolated OPA exited")
                try:
                    with opener.open(base + "/health", timeout=0.2) as response:
                        if response.status != 200:
                            raise RuntimeError("isolated OPA health not ready")
                    if proc.poll() is None:
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                raise RuntimeError("isolated OPA did not become ready")
            for size in (10, 1000):
                values: dict[str, list[float]] = {"cli": [], "native_http": []}
                for _ in range(count):
                    numbers = [rng.randrange(-100, 101) for _ in range(size)]
                    raw = json.dumps(
                        {"numbers": numbers}, separators=(",", ":")
                    ).encode()
                    expected = sum(numbers) + 7
                    order = list(values)
                    rng.shuffle(order)
                    for carrier in order:
                        start = time.perf_counter_ns()
                        if carrier == "cli":
                            result = subprocess.run(
                                [str(opa), "eval", "--stdin-input", "--format", "raw",
                                 "--data", str(policy), "--data", str(data),
                                 "data.demo.result"],
                                input=raw, capture_output=True, check=True, timeout=3,
                            )
                            actual = json.loads(result.stdout)
                        else:
                            request = urllib.request.Request(
                                base + "/v1/data/demo/result",
                                data=b'{"input":' + raw + b"}",
                                headers={"Content-Type": "application/json"},
                            )
                            with opener.open(request, timeout=3) as response:
                                actual = json.load(response)["result"]
                        values[carrier].append((time.perf_counter_ns() - start) / 1e6)
                        if type(actual) is not int or actual != expected:
                            raise ValueError("native arithmetic observation differs")
                observations.append({
                    "inputCount": size,
                    "samplesPerCarrier": count,
                    "medianMs": {
                        k: round(statistics.median(v), 3) for k, v in values.items()
                    },
                    "p95NearestRankMs": {
                        k: round(percentile95(v), 3) for k, v in values.items()
                    },
                    "exactArithmeticParity": True,
                })
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    return observations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opa", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=24, choices=range(4, 101))
    args = parser.parse_args()
    opa = args.opa.resolve(strict=True)
    version = subprocess.check_output([str(opa), "version"], text=True).splitlines()[0]
    print(json.dumps({
        "standing": "SYNTHETIC_NON_AUTHORIZING_CARRIER_COMPARISON",
        "providerVersion": version,
        "results": benchmark(opa, args.samples),
    }, indent=2))


if __name__ == "__main__":
    main()
