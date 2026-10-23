#!/usr/bin/env python3
"""Materialize the bounded flat Artifact index for Experimental Episode R1.

Run this script with the frozen Artifact PyArrow carrier, not the meta/next
environment:

  /opt/ordivon/external/pyarrow/25.0.1/python \
    meta/next/scripts/experimental_episode_index_r1.py \
    --input runtime.jsonl --input harness.jsonl --output episode-index.parquet

The output is a rebuildable interchange projection, not owner truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA = pa.schema(
    [
        ("episode_id", pa.string(), False),
        ("projection_digest", pa.string(), False),
        ("profile_id", pa.string(), False),
        ("data_class", pa.string(), False),
        ("anchor_owner_id", pa.string(), False),
        ("anchor_object_kind", pa.string(), False),
        ("anchor_object_id", pa.string(), False),
        ("source_record_digest", pa.string(), False),
    ]
)


def materialize(inputs: list[Path], output: Path) -> dict[str, int]:
    rows: list[dict[str, object]] = []
    for path in inputs:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                episode = json.loads(line)
                anchor = episode["anchor"]
                rows.append(
                    {
                        "episode_id": episode["episodeId"],
                        "projection_digest": episode["projectionDigest"],
                        "profile_id": episode["profileId"],
                        "data_class": episode["dataClass"],
                        "anchor_owner_id": anchor["ownerId"],
                        "anchor_object_kind": anchor["objectKind"],
                        "anchor_object_id": anchor["objectId"],
                        "source_record_digest": anchor["sourceRecordDigest"],
                    }
                )
    rows.sort(key=lambda row: str(row["episode_id"]))
    episode_ids = [str(row["episode_id"]) for row in rows]
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode_id is not unique across supplied inputs")
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output, compression="zstd")
    return {"rows": table.num_rows, "columns": table.num_columns}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(args.input, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
