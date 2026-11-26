"""Reuse the exact Runtime PG fixture without changing its tracked owner source."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    original = ROOT / "services/runtime/crates/ordivon-runtime-mcp/tests/pg_vertical.rs"
    generated = original.with_name("gateway_r21_generated_pg_stream.rs")
    runtime = ROOT / "services/runtime/Cargo.toml"
    manifest = HERE / "Cargo.toml"
    meta = json.loads(
        subprocess.check_output(
            [
                "cargo",
                "metadata",
                "--locked",
                "--offline",
                "--no-deps",
                "--format-version",
                "1",
                "--manifest-path",
                str(manifest),
            ]
        )
    )
    probe = pathlib.Path(meta["target_directory"]) / "debug/ordivon-gateway-read-only-probe"
    assert probe.is_file(), "build the Gateway probe first"
    env = dict(os.environ, ORDIVON_GATEWAY_STREAM_PROBE=str(probe))
    # Exclusive creation; never edit or restore a peer's tracked source.
    content = original.read_bytes() + b"\n" + (HERE / "qualify_pg_stream.rs").read_bytes()
    with generated.open("xb") as out:
        out.write(content)
    try:
        subprocess.run(
            [
                "cargo",
                "build",
                "--locked",
                "--offline",
                "--manifest-path",
                str(runtime),
                "-p",
                "ordivon-runtime-core",
                "--no-default-features",
                "--features",
                "postgres-registry-admission",
                "--bin",
                "ordivon-runtime-runner",
            ],
            env=env,
            check=True,
        )
        subprocess.run(
            [
                "cargo",
                "test",
                "--locked",
                "--offline",
                "--manifest-path",
                str(runtime),
                "-p",
                "ordivon-runtime-mcp",
                "--no-default-features",
                "--features",
                "postgres-runtime",
                "--test",
                generated.stem,
                "gateway_r21_real_pg_stream_consumer",
                "--",
                "--ignored",
                "--exact",
                "--nocapture",
            ],
            env=env,
            check=True,
        )
    finally:
        if generated.read_bytes() == content:
            generated.unlink()
        else:
            raise RuntimeError("generated fixture changed; refuse deletion")


if __name__ == "__main__":
    main()
