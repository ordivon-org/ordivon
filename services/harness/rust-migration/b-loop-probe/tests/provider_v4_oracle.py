#!/usr/bin/env python3
"""Execute the CURRENT Python ProviderRecordV4 validation as the oracle."""
from __future__ import annotations

import random

from anc_canonical import canonical_bytes
from ordivon_harness.ordivon.continuity_records import (
    HarnessProviderCallRecordV4, build_provider_call_record_v4
)
from ordivon_harness.protocol import (
    HarnessProviderCallStatus, HarnessProviderCallSource
)
rng = random.Random(20261110)
d = lambda x: "sha256:" + x * 64

def emit(value):
    try:
        result = HarnessProviderCallRecordV4.from_dict(value)
        canonical = canonical_bytes(result.to_dict()).hex()
        print("\t".join(("V", "1", canonical, result.digest, result.status.value, str(result.turn_sequence), str(result.claim_generation))))
    except (TypeError, ValueError):
        print("\t".join(("V", "0", canonical_bytes(value).hex(), "-", "-", "-", "-")))

for i in range(8):
    status = (
        HarnessProviderCallStatus.CLAIMED,
        HarnessProviderCallStatus.DISPATCHING,
        HarnessProviderCallStatus.COMPLETED,
        HarnessProviderCallStatus.FAILED,
        HarnessProviderCallStatus.UNKNOWN,
    )[i % 5]
    failure = status in (HarnessProviderCallStatus.FAILED, HarnessProviderCallStatus.UNKNOWN)
    completed = status is HarnessProviderCallStatus.COMPLETED
    record = build_provider_call_record_v4(
        provider_call_id=f"provider-call:{i}",
        harness_run_id="harness-run:test",
        binding_digest=d("a"),
        source_kind=(HarnessProviderCallSource.ASSIGNMENT if i % 2 == 0 else HarnessProviderCallSource.SNAPSHOT),
        source_digest=d("b"), source_object_digest=d("c"),
        state_object_digest=d("d"), turn_id=f"turn:{i}",
        turn_sequence=i+1, request_digest=d("e"),
        request_object_digest=None if i % 2 else d("f"),
        provider_request_digest=d("0"),
        adapter_id="provider:东京", requested_model_id="model:🚀",
        holder_id="agent:α", generation=1 if status is HarnessProviderCallStatus.CLAIMED else 2,
        status=status,
        result_digest=d("1") if completed else None,
        result_object_digest=d("2") if completed and i % 2 else None,
        failure_digest=d("3") if failure else None,
        failure_object_digest=d("4") if failure else None,
        previous_record_digest=None if status is HarnessProviderCallStatus.CLAIMED else d("5"),
        issued_at_ms=100, expires_at_ms=500, recorded_at_ms=600,
    )
    source = record.to_dict()
    emit(source)
    changes = {
        "schemaVersion": [3, False, "4"],
        "kind": ["wrong", None],
        "recordId": ["wrong", " harness-provider-call-record:trailing "],
        "providerCallId": ["broken", ""],
        "harnessRunId": ["wrong", None],
        "bindingDigest": ["bad", "sha256:" + "A"*64],
        "sourceKind": ["broken"],
        "sourceDigest": ["bad"],
        "sourceObjectDigest": ["bad"],
        "stateObjectDigest": ["bad"],
        "turnId": ["wrong"],
        "turnSequence": [-1, 0, True],
        "requestDigest": ["bad"],
        "requestObjectDigest": ["bad"],
        "providerRequestDigest": ["bad"],
        "adapterId": [None, "  "],
        "requestedModelId": [None, " model "],
        "holderId": [" "],
        "claimGeneration": [0, -1, True],
        "status": ["lost", "pending"],
        "resultDigest": ["bad", d("6")],
        "resultObjectDigest": ["bad", d("6")],
        "failureDigest": ["bad", d("6")],
        "failureObjectDigest": ["bad", d("6")],
        "previousRecordDigest": ["bad", None],
        "issuedAtMs": [-1, "100"],
        "expiresAtMs": [100, -10, "500"],
        "recordedAtMs": [-1, "600"],
    }
    for field, variants in changes.items():
        for variant in variants:
            changed = dict(source)
            changed[field] = variant
            emit(changed)
    for key in rng.sample(list(source), 4):
        changed = dict(source)
        del changed[key]
        emit(changed)
    changed = dict(source); changed["nonexistent"] = "extra"; emit(changed)


# Python's V4 validator permits integers beyond Rust u64. These are
# legitimate source records; the Rust projection must not reject or saturate.
for length in (19, 20, 65, 120, 1024, 4096):
    large = int("9" * length)
    for field_name in ("turnSequence", "claimGeneration", "recordedAtMs"):
        wide = dict(source)
        wide[field_name] = large
        emit(wide)
    wide_expiry = dict(source)
    wide_expiry["expiresAtMs"] = large
    emit(wide_expiry)
    wide_time_pair = dict(source)
    wide_time_pair["issuedAtMs"] = large
    wide_time_pair["expiresAtMs"] = 10 ** (length + 1)
    emit(wide_time_pair)
    invalid_version = dict(source)
    invalid_version["schemaVersion"] = large
    emit(invalid_version)
    invalid_negative = dict(source)
    invalid_negative["issuedAtMs"] = -large
    emit(invalid_negative)

# Python str.strip() recognizes C0 0x1C-0x1F as whitespace;
# Rust Unicode White_Space deliberately has a different set.
# These are adversarial real source-domain records, not made-up rules.
for codepoint in (0x1C, 0x1D, 0x1E, 0x1F, 0x85, 0xA0, 0x200B, 0x2028, 0xFEFF):
    for field_name in ("adapterId", "requestedModelId", "holderId"):
        candidate = dict(source)
        candidate[field_name] = chr(codepoint) + source[field_name]
        emit(candidate)
