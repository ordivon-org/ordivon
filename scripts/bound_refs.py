#!/usr/bin/env python
from __future__ import annotations

import hashlib
from copy import deepcopy

import rfc8785


def _sha256_jcs(value: object) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def effect_payload_ref(intent: dict) -> str:
    return _sha256_jcs(intent["effect"]["payload"])


def occurrence_projection(intent: dict) -> dict:
    artifact = intent.get("artifact")
    projection = {
        "schemaVersion": 2,
        "intentId": intent["intentId"],
        "provider": intent["carrier"]["provider"],
        "accountRef": intent["carrier"]["accountRef"],
        "effectName": intent["effect"]["name"],
        "effectPayloadRef": effect_payload_ref(intent),
    }
    if isinstance(artifact, dict):
        projection["artifact"] = {
            "sha256": artifact.get("sha256"),
            "releaseReady": artifact.get("releaseReady"),
            "trustStanding": artifact.get("trustStanding"),
            "sourceRef": artifact.get("sourceRef"),
        }
    else:
        # Preserve the R6 occurrence identity for non-artifact intents.
        projection["artifactSha256"] = None
    return projection


def occurrence_ref(intent: dict) -> str:
    return _sha256_jcs(occurrence_projection(intent))


def provider_observation_ref(observation: dict) -> str:
    value = deepcopy(observation)
    value.pop("observationRef", None)
    return _sha256_jcs(value)


def effect_authority_ref(authority: dict) -> str:
    value = deepcopy(authority)
    value.pop("authorityRef", None)
    return _sha256_jcs(value)
