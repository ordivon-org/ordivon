"""Directional native v1 artifact ABI oracle against the actual Python Gateway model."""

from __future__ import annotations

import random

from qualify_chunk import REF, fixture, oracle

from ordivon_gateway.contracts import ArtifactChunk


def add_abi_cases(add):
    def case(d, r, v, reference=REF):
        result = oracle(reference, d, r, v)
        if result["standing"] == "qualified":
            chunk = ArtifactChunk(
                operation_ref=reference,
                owner_id=result["owner"],
                native_id=result["native_id"],
                artifact_id=result["artifact_id"],
                offset=result["offset"],
                next_offset=result["next_offset"],
                eof=result["eof"],
                digest=result["digest"],
                content=result["content"],
            )
            expected = {"standing": "qualified", "chunk": chunk.model_dump(mode="json")}
        else:
            expected = result
        add(
            "artifact_v1",
            {"operationRef": reference, "descriptor": d, "request": r, "response": v},
            expected,
        )

    rng = random.Random(20261126)
    for _ in range(512):
        text = "".join(rng.choice("abc中文🙂é") for _ in range(rng.randrange(1, 40)))
        start = rng.randrange(len(text))
        end = rng.randrange(start + 1, len(text) + 1)
        d, r, v = fixture(text, start, end)
        case(d, r, v)
        case(d, r, {**v, "artifactId": "foreign"})
    for text in ("", "中文", "abc"):
        d, r, v = fixture(text)
        case(d, r, v)
        case(d, r, v, "bad-ref")
        case(d, r, {**v, "eof": "true"})
