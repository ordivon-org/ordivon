"""R6 browser-evidence to Agent-observer experimental task projection.

A browser receipt is supplied by its natural Web consumer. This module
does not navigate browsers or claim human-observer consequences.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .creative_protocol import VARIANTS
from .grounded_contracts import canonical_digest


def _qa_schema(question_ids: Sequence[str], option_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "answers": {
                "type": "array",
                "minItems": len(question_ids),
                "maxItems": len(question_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "questionId": {"type": "string", "enum": list(question_ids)},
                        "optionId": {"type": "string", "enum": list(option_ids)},
                        "evidenceIds": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
                    },
                    "required": ["questionId", "optionId", "evidenceIds"],
                },
            }
        },
        "required": ["answers"],
    }


def _receipt_representatives(receipt: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    reps = receipt.get("representativeEncounters")
    if not isinstance(reps, list):
        raise ValueError("Web receipt lacks representative encounters")
    result = {str(item["variantId"]): item for item in reps if isinstance(item, dict) and item.get("variantId")}
    for variant in VARIANTS:
        if variant not in result:
            raise ValueError(f"Web receipt lacks representative encounter for {variant}")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict) or not integrity.get("allAssignmentsUnique") or not integrity.get("allExposuresRealizedExactlyOnce") or not integrity.get("allPropensitiesExplicit") or not integrity.get("allVariantDigestsBound"):
        raise ValueError("Web receipt failed encounter integrity")
    return result


def build_observer_bundle(*, protocol: Mapping[str, Any], web_receipts: Sequence[Mapping[str, Any]], replicates: int | None = None) -> dict[str, Any]:
    mechanism_specs = {str(item["mechanismId"]): item for item in protocol["mechanisms"]}
    # Prefer explicit manifest experiment binding over filename/order inference.
    bound: dict[str, Mapping[str, Any]] = {}
    for mechanism_id, spec in mechanism_specs.items():
        experiment_id = spec["manifest"]["experimentId"]
        match = next((receipt for receipt in web_receipts if receipt.get("experimentId") == experiment_id), None)
        if match is None:
            raise ValueError(f"missing Web receipt for mechanism {mechanism_id}")
        bound[mechanism_id] = match
    replicate_count = int(replicates or protocol.get("replicatesPerEncounter", 8))
    tasks = []
    for mechanism_id, spec in mechanism_specs.items():
        reps = _receipt_representatives(bound[mechanism_id])
        questions = spec["oracle"]["questions"]
        public_questions = [
            {key: question[key] for key in ("questionId", "stage", "question", "options")}
            for question in questions
        ]
        for variant in VARIANTS:
            encounter = reps[variant]
            viewport_evidence = encounter.get("viewportEvidence")
            if not isinstance(viewport_evidence, list) or not viewport_evidence:
                raise ValueError(f"no viewport evidence for {mechanism_id}/{variant}")
            evidence = [
                {
                    "evidenceId": str(item["evidenceId"]),
                    "modality": "browser-visible-text",
                    "sourceId": f"web-receipt:{bound[mechanism_id]['receiptDigest']}:{variant}",
                    "locator": {"encounterMode": "initial-viewport-no-scroll", "top": item["top"], "bottom": item["bottom"]},
                    "observed": f"{item['heading']}: {item['text']}",
                }
                for item in viewport_evidence
            ]
            task = {
                "taskId": f"r6c:{mechanism_id}:{variant}",
                "kind": "browser-grounded-adaptation-qa",
                "replicates": replicate_count,
                "systemPrompt": (
                    "You are a bounded observer of one initial no-scroll browser encounter. Answer only from the supplied browser-visible evidence. "
                    "Do not assume facts from later page content, prior runs, general knowledge, or the question wording. If the visible evidence does not establish the answer, choose O4 and cite no evidence. "
                    "For a substantive answer, cite every supplied evidence item needed to establish it."
                ),
                "userPayload": {
                    "encounter": {
                        "observerClass": protocol["observerClass"],
                        "mode": "initial-viewport-no-scroll",
                        "screenshotDigest": encounter["screenshotDigest"],
                        "viewportEvidenceDigest": encounter["viewportEvidenceDigest"],
                    },
                    "artifactEvidence": evidence,
                    "questions": public_questions,
                },
                "resultSchema": _qa_schema([item["questionId"] for item in questions], ["O1", "O2", "O3", "O4"]),
                "oracle": {
                    "answers": {item["questionId"]: item["answer"] for item in questions},
                    "stages": {item["questionId"]: item["stage"] for item in questions},
                    "requiredEvidenceAll": {item["questionId"]: item["requiredEvidenceAll"] for item in questions},
                },
                "scope": "Agent-observer consequence over exact browser initial-viewport evidence; not human consequence",
            }
            tasks.append(task)
    provider_tasks = []
    oracle = {}
    for task in tasks:
        oracle[task["taskId"]] = task["oracle"]
        provider_tasks.append({key: task[key] for key in ("taskId", "kind", "replicates", "systemPrompt", "userPayload", "resultSchema", "scope")})
    bundle = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-creative-alpha-observer-bundle",
        "protocolDigest": protocol.get("protocolDigest") or protocol.get("holdoutProtocolDigest"),
        "tasks": provider_tasks,
        "oracle": oracle,
        "interpretationBoundary": "Provider sees browser-grounded evidence and questions but never the oracle. Scores are Agent-observer consequences, not human-response evidence.",
    }
    bundle["bundleDigest"] = canonical_digest(bundle)
    return bundle


def build_holdout_observer_bundle(*, holdout_protocol: Mapping[str, Any], web_receipt: Mapping[str, Any], replicates: int = 8) -> dict[str, Any]:
    visible_shape = {
        "protocolDigest": holdout_protocol["holdoutProtocolDigest"],
        "observerClass": "deepseek-flash-agent-observer",
        "replicatesPerEncounter": replicates,
        "mechanisms": [
            {
                "mechanismId": "C",
                "manifest": holdout_protocol["manifest"],
                "oracle": holdout_protocol["oracle"],
            }
        ],
    }
    return build_observer_bundle(protocol=visible_shape, web_receipts=[web_receipt], replicates=replicates)
