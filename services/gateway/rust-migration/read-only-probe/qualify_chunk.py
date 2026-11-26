"""Native byte-window contract, independent hashlib and source ABI witnesses."""

from __future__ import annotations

import hashlib
import random

from pydantic import ValidationError
from qualify_semantics import independent_descriptor

from ordivon_gateway.capabilities.execution.observations import ExecutionObservationMethods
from ordivon_gateway.contracts import ExecutionObservation
from ordivon_gateway.logic.execution_refs import GatewayError, parse_execution_ref

REF = "ordivon-exec:v1:runtime.linux:job-a"
MAX = 2**64 - 1


def digest(content):
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def fixture(text, start=0, end=None):
    if end is None:
        end = len(text)
    total = len(text.encode("utf-8"))
    offset = len(text[:start].encode("utf-8"))
    selected = text[start:end]
    next_offset = offset + len(selected.encode("utf-8"))
    d = {
        "artifactId": "opaque-id",
        "attemptId": "attempt-not-derived-from-id",
        "kind": "stdout",
        "digest": digest(text),
        "retainedBytes": total,
        "truncated": False,
    }
    r = {"artifactId": "opaque-id", "offset": offset, "maxBytes": max(1, next_offset - offset)}
    v = {
        "jobId": "job-a",
        "artifactId": "opaque-id",
        "digest": d["digest"],
        "offset": offset,
        "nextOffset": next_offset,
        "eof": next_offset == total,
        "content": selected,
    }
    return d, r, v


def oracle(ref, d, r, v):
    def no(reason):
        return {"standing": "unobserved", "reason": reason}

    def uint(x):
        return type(x) is int and 0 <= x <= MAX

    try:
        owner, job = parse_execution_ref(ref)
    except GatewayError:
        return no("invalid_operation_ref")
    if not independent_descriptor({"artifacts": [d]}, 1)["metadata_complete"]:
        return no("unqualified_descriptor")
    if (
        not isinstance(r, dict)
        or r.keys() != {"artifactId", "offset", "maxBytes"}
        or not isinstance(r["artifactId"], str)
        or not all(uint(r[k]) for k in ("offset", "maxBytes"))
        or r["artifactId"] != d["artifactId"]
        or not 1 <= r["maxBytes"] <= 1048576
        or r["offset"] > d["retainedBytes"]
        or r["offset"] + r["maxBytes"] > MAX
    ):
        return no("invalid_request")
    if (
        not isinstance(v, dict)
        or v.keys() != {"jobId", "artifactId", "digest", "offset", "nextOffset", "eof", "content"}
        or not all(isinstance(v[k], str) for k in ("jobId", "artifactId", "digest", "content"))
        or not all(uint(v[k]) for k in ("offset", "nextOffset"))
        or type(v["eof"]) is not bool
    ):
        return no("invalid_window")
    if (v["jobId"], v["artifactId"], v["digest"]) != (job, r["artifactId"], d["digest"]):
        return no("mismatched_window_identity")
    if v["offset"] != r["offset"] or not (
        v["offset"] <= v["nextOffset"] <= min(d["retainedBytes"], r["offset"] + r["maxBytes"])
    ):
        return no("invalid_range")
    if v["eof"] != (v["nextOffset"] == d["retainedBytes"]) or (
        not v["eof"] and v["nextOffset"] == v["offset"]
    ):
        return no("invalid_progress_or_eof")
    if len(v["content"].encode("utf-8")) != v["nextOffset"] - v["offset"]:
        return no("invalid_byte_length")
    full = v["offset"] == 0 and v["eof"]
    if full and digest(v["content"]) != v["digest"]:
        return no("full_digest_mismatch")
    return {
        "standing": "qualified",
        "owner": owner,
        "native_id": job,
        "artifact_id": v["artifactId"],
        "digest": v["digest"],
        "offset": v["offset"],
        "next_offset": v["nextOffset"],
        "eof": v["eof"],
        "content": v["content"],
        "full_digest_verified": True if full else None,
    }


def add_chunk_cases(add):
    def case(d, r, v, ref=REF):
        add(
            "artifact_chunk",
            {"operationRef": ref, "descriptor": d, "request": r, "response": v},
            oracle(ref, d, r, v),
        )

    for text in ("", "a", "中文🙂", "e\u0301", "\x00\n", "𐍈"):
        d, r, v = fixture(text)
        case(d, r, v)
        case(d, r, {**v, "digest": "sha256:" + "z" * 64})
        case(d, r, {**v, "content": "x" * len(text.encode("utf-8"))})
        case(d, r, {**v, "eof": False})
        for k in ("offset", "maxBytes"):
            for x in (None, True, -1, 1.0, MAX, MAX + 1):
                case(d, {**r, k: x}, v)
        case(d, r, v, "bad-ref")
    rng = random.Random(20261126)
    for _ in range(1024):
        text = "".join(rng.choice("abc中文🙂é𐍈\n") for _ in range(rng.randrange(1, 30)))
        start = rng.randrange(len(text) + 1)
        end = rng.randrange(start, len(text) + 1)
        if start == end and end < len(text):
            end += 1
        d, r, v = fixture(text, start, end)
        case(d, r, v)
        key, value = rng.choice(
            (
                ("jobId", "wrong"),
                ("artifactId", "wrong"),
                ("nextOffset", 0),
                ("offset", True),
                ("eof", not v["eof"]),
                ("content", v["content"] + "x"),
                ("digest", "sha256:" + "b" * 64),
                ("extra", None),
            )
        )
        case(d, r, {**v, key: value})
    d, r, v = fixture("abc")
    case({**d, "retainedBytes": MAX}, {**r, "offset": MAX, "maxBytes": 2}, v)


async def qualify_legacy_abi():
    # The old strict output model is a real consumer schema, not a generic JSON object.
    base = ExecutionObservation(
        operation_ref=REF,
        owner_id="runtime.linux",
        native_id="job-a",
        capability="execution.linux",
        state="succeeded",
        terminal=True,
    )
    for field in ("artifact_descriptors", "result_available", "semantic_completion_evaluated"):
        try:
            ExecutionObservation.model_validate({**base.model_dump(), field: []})
        except ValidationError as exc:
            assert any(e["type"] == "extra_forbidden" for e in exc.errors())
        else:
            raise AssertionError("legacy strict model unexpectedly accepts new field")
    d, r, v = fixture("abc")
    # Malformed same-length test reply, not a claim about natural Runtime bytes.
    fake = {**v, "content": "xyz"}

    class Caller:
        async def call_tool(self, owner, tool, args):
            assert (owner, tool) == ("runtime.linux", "artifact.read")
            assert args["jobId"] == "job-a"
            return fake

    result = await ExecutionObservationMethods(Caller(), {}).artifact_read(
        REF, r["artifactId"], offset=r["offset"], max_bytes=r["maxBytes"]
    )
    assert result.content == "xyz" and result.digest == d["digest"]
    assert oracle(REF, d, r, fake) == {"standing": "unobserved", "reason": "full_digest_mismatch"}
    print(
        "LEGACY_ABI_STRICT_EXTRA_REJECTED 3; MALFORMED_FIXTURE_SOURCE_ACCEPTS_SAME_LENGTH_CORRUPTION",
        flush=True,
    )
