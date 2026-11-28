"""Adversarial decision-witness refinement; real producer exercised separately."""

from __future__ import annotations

import hashlib
import itertools
import json
import uuid
from dataclasses import replace

import pytest

from ordivon_gateway.security.policy_standing import (
    MAX_AGE_MS,
    StandingExpectation,
    decode_object,
    qualify_decision,
    qualify_pair,
)
from ordivon_gateway.security.standing_transport import observe_pair

NOW = 2_000_000
INSTANCE = str(uuid.UUID(int=1))
REQ = str(uuid.UUID(int=2))
OTHER = str(uuid.UUID(int=3))


@pytest.fixture
def expected():
    return StandingExpectation.from_document(
        {
            "policySha256": "sha256:" + "a" * 64,
            "releaseRevision": "b" * 40,
            "issuer": "https://issuer.test",
            "permitPrincipal": "principal:cf-access:" + "c" * 64,
            "denyPrincipal": "principal:cf-access:" + "d" * 64,
            "messageRef": "message:synthetic:exact",
        }
    )


def witness(expected, *, permit=True, request_id=REQ):
    return {
        "decision": permit,
        "context": {
            "ordivonPolicyStanding": {
                "schemaVersion": 1,
                "standing": "OBSERVED_FOR_DECISION",
                "requestId": request_id,
                "instanceId": INSTANCE,
                "policySha256": expected.policy_sha256,
                "policyDataCommitment": "hmac-sha256:" + "e" * 64,
                "inputSha256": "sha256:"
                + hashlib.sha256(expected.payload(permit=permit)).hexdigest(),
                "declaredReleaseRevision": expected.release_revision,
                "evaluatedAtEpochMs": NOW,
            }
        },
    }


def qualify(expected, row, **kw):
    args = dict(
        permit=True,
        request_id=REQ,
        response_request_id=REQ,
        cache_control="no-store",
        started_ms=NOW - 10,
        received_ms=NOW + 10,
    )
    args.update(kw)
    return qualify_decision(expected, response=json.dumps(row).encode(), **args)


def test_exact_pair_has_no_secret_or_subject_projection(expected):
    permit = qualify(expected, witness(expected))
    deny = qualify(
        expected,
        witness(expected, permit=False, request_id=OTHER),
        permit=False,
        request_id=OTHER,
        response_request_id=OTHER,
    )
    result = qualify_pair(permit, deny, now_ms=NOW + 50)
    assert result["standing"] == "OBSERVED_FOR_EXACT_READ_PAIR"
    assert set(result) == {
        "standing",
        "permitRequestId",
        "denyRequestId",
        "instanceId",
        "evaluatedAtEpochMs",
        "truthBoundary",
    }
    a, b = (json.loads(expected.payload(permit=p)) for p in (True, False))
    assert a["resource"] == b["resource"] and a["action"] == b["action"]
    assert a["subject"]["id"] != b["subject"]["id"]
    assert a["resource"]["properties"]["requestedSelectors"] == {"messageRef": expected.message_ref}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schemaVersion", True),
        ("schemaVersion", 1.0),
        ("standing", "UNKNOWN"),
        ("requestId", OTHER),
        ("instanceId", "bad"),
        ("policySha256", "sha256:" + "f" * 64),
        ("policyDataCommitment", "sha256:" + "e" * 64),
        ("inputSha256", "sha256:" + "f" * 64),
        ("declaredReleaseRevision", None),
        ("declaredReleaseRevision", "c" * 40),
        ("evaluatedAtEpochMs", True),
        ("evaluatedAtEpochMs", NOW - 2000),
        ("evaluatedAtEpochMs", NOW + 2000),
    ],
)
def test_each_bad_witness_field_fails_closed(expected, field, value):
    row = witness(expected)
    row["context"]["ordivonPolicyStanding"][field] = value
    with pytest.raises(ValueError):
        qualify(expected, row)


@pytest.mark.parametrize(
    "change",
    [
        {"decision": 1},
        {"error": "unexpected"},
        {"decision": False},
        {"context": {}},
        {"context": None},
        {"context": {"obligations": [{"required": True}]}},
    ],
)
def test_unqualified_decision_never_accepted(expected, change):
    row = witness(expected)
    row.update(change)
    with pytest.raises(ValueError):
        qualify(expected, row)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"a":{"x":1,"x":2}}',
        b'{"n":NaN}',
        b'{"n":1e999}',
        b'{"x":"\xff"}',
        rb'{"x":"\ud800"}',
        b"[]",
        b" " * 65537,
    ],
)
def test_ambiguous_or_unbounded_json_rejected(raw):
    with pytest.raises(ValueError):
        decode_object(raw)


def test_pair_conjunctive_64_states(expected):
    p = qualify(expected, witness(expected))
    d = qualify(
        expected,
        witness(expected, permit=False, request_id=OTHER),
        permit=False,
        request_id=OTHER,
        response_request_id=OTHER,
    )
    for (
        same_instance,
        same_data,
        different_request,
        different_input,
        ordered,
        fresh,
    ) in itertools.product((False, True), repeat=6):
        q = replace(
            d,
            instance_id=p.instance_id if same_instance else OTHER,
            policy_data_commitment=p.policy_data_commitment
            if same_data
            else "hmac-sha256:" + "f" * 64,
            request_id=d.request_id if different_request else p.request_id,
            input_sha256=d.input_sha256 if different_input else p.input_sha256,
            evaluated_at_ms=NOW if ordered else NOW - 1,
        )
        now = NOW + 1 if fresh else NOW + MAX_AGE_MS + 1
        if all((same_instance, same_data, different_request, different_input, ordered, fresh)):
            assert qualify_pair(p, q, now_ms=now)["standing"] == "OBSERVED_FOR_EXACT_READ_PAIR"
        else:
            with pytest.raises(ValueError):
                qualify_pair(p, q, now_ms=now)


def test_response_header_correlation_and_cache_and_clock(expected):
    row = witness(expected)
    for change in (
        {"response_request_id": OTHER},
        {"cache_control": "public"},
        {"received_ms": NOW - 11},
        {"received_ms": NOW + MAX_AGE_MS + 1},
    ):
        with pytest.raises(ValueError):
            qualify(expected, row, **change)


def test_unqualified_operator_config_rejected(expected):
    document = {
        "policySha256": expected.policy_sha256,
        "releaseRevision": expected.release_revision,
        "issuer": expected.issuer,
        "permitPrincipal": expected.permit_principal,
        "denyPrincipal": expected.deny_principal,
        "messageRef": expected.message_ref,
    }
    for change in (
        {"denyPrincipal": expected.permit_principal},
        {"denyPrincipal": "principal:garbage"},
        {"messageRef": "topic:wrong"},
        {"releaseRevision": "latest"},
        {"policySha256": "missing"},
        {"extra": True},
    ):
        with pytest.raises(ValueError):
            StandingExpectation.from_document(document | change)


def test_transport_refuses_redirect_and_never_attempts_second_probe(expected):
    class Response:
        status_code = 302

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    class Session:
        calls = 0

        def post(self, endpoint, **kwargs):
            assert endpoint == "https://127.0.0.1:18787/access/v1/evaluation"
            assert kwargs["allow_redirects"] is False and kwargs["stream"] is True
            self.calls += 1
            return Response()

    session = Session()
    with pytest.raises(ValueError):
        observe_pair(expected, bearer="test-only-" + "x" * 40, session=session)
    assert session.calls == 1
