from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .grounded_meaning import canonical_digest
from .research_validity import seed_commitment


VARIANTS = ("explicit-chain", "fragmented", "evidence-delayed")
PRIMARY_TREATMENT = "explicit-chain"
PRIMARY_CONTROL = "fragmented"
ABSTAIN_OPTION = "O4"


def _rng(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _mechanism(seed: str, mechanism_id: str) -> dict[str, Any]:
    rng = _rng(seed)
    gauges = ["Neral", "Tovin", "Keral", "Miran", "Sovel", "Lethin"]
    latch_colors = ["amber", "violet", "copper", "silver", "indigo", "crimson"]
    chambers = ["blue chamber", "ceramic chamber", "north chamber", "glass chamber", "inner chamber", "cooling chamber"]
    spindles = ["Varo spindle", "Kelm rotor", "Sorin wheel", "Daro shaft", "Mek spindle", "Teral rotor"]
    trigger = rng.choice([5, 6, 7, 8, 9])
    safe_temp = rng.choice([36, 38, 40, 42, 44])
    gauge = rng.choice(gauges)
    latch = f"{rng.choice(latch_colors)} latch"
    chamber = rng.choice(chambers)
    spindle = rng.choice(spindles)
    facts = {
        "F1": {
            "heading": "Trigger",
            "text": f"When the fictitious {gauge} gauge reaches {trigger}, the {latch} opens; below {trigger}, it remains closed. The gauge is only the upstream trigger and does not directly move the final actuator.",
        },
        "F2": {
            "heading": "Transfer",
            "text": f"The {latch} controls coolant access to the {chamber}. An open latch permits coolant entry; a closed or mechanically jammed latch blocks coolant even when the {gauge} gauge has reached its trigger.",
        },
        "F3": {
            "heading": "Cooling",
            "text": f"Coolant entering the {chamber} lowers it below {safe_temp} degrees. If coolant does not enter, the chamber remains above that threshold in the situations described here. No second cooling path is defined.",
        },
        "F4": {
            "heading": "Permission boundary",
            "text": f"The {spindle} may rotate safely only when the {chamber} is below {safe_temp} degrees. At or above {safe_temp} degrees it must remain stopped, regardless of the upstream gauge or latch state.",
        },
        "F5": {
            "heading": "Causal boundary",
            "text": f"A {gauge} reading of {trigger} is not by itself permission for the {spindle} to rotate. Latch opening, coolant entry, and chamber cooling must still succeed; an intermediate failure can leave the actuator unsafe.",
        },
        "D1": {
            "heading": "Non-causal identifier",
            "text": f"A maintenance plate beside the {chamber} carries the code {rng.choice(['PX-14','QR-22','LM-31','VK-08'])}. It identifies the assembly but has no causal role in the gauge, latch, coolant, temperature, or spindle sequence.",
        },
        "D2": {
            "heading": "Non-causal service signal",
            "text": f"A service lamp near the {spindle} records inspection hours. Its color may change during maintenance, but it neither opens the {latch} nor changes coolant flow or the {safe_temp}-degree safety boundary.",
        },
    }
    orders = {
        "explicit-chain": ["F1", "F2", "F3", "F4", "F5", "D1", "D2"],
        "fragmented": ["D1", "F5", "D2", "F3", "F4", "F2", "F1"],
        "evidence-delayed": ["F2", "F3", "F4", "D1", "D2", "F5", "F1"],
    }
    options_trigger = {"O1": str(trigger), "O2": str(safe_temp), "O3": str(trigger + 3), "O4": "The visible evidence does not establish this"}
    questions = [
        {
            "questionId": "Q1",
            "stage": "perception",
            "question": f"What {gauge} gauge reading opens the {latch}?",
            "options": options_trigger,
            "answer": "O1",
            "requiredEvidenceAll": ["F1"],
        },
        {
            "questionId": "Q2",
            "stage": "comprehension",
            "question": f"What does a mechanically jammed closed {latch} do to coolant flow?",
            "options": {"O1": "It blocks coolant entry", "O2": "It forces coolant entry", "O3": "It directly cools the chamber", "O4": "The visible evidence does not establish this"},
            "answer": "O1",
            "requiredEvidenceAll": ["F2"],
        },
        {
            "questionId": "Q3",
            "stage": "comprehension",
            "question": f"Why does coolant matter to the {safe_temp}-degree boundary?",
            "options": {"O1": "It lowers the chamber below the boundary", "O2": "It raises the gauge reading", "O3": "It changes the service-lamp color", "O4": "The visible evidence does not establish this"},
            "answer": "O1",
            "requiredEvidenceAll": ["F3"],
        },
        {
            "questionId": "Q4",
            "stage": "adaptation",
            "question": f"The {gauge} gauge reaches {trigger}, but the {latch} is mechanically jammed closed and the chamber remains warm. May the {spindle} rotate safely?",
            "options": {"O1": "Yes", "O2": "No", "O3": "Only because the service lamp can override it", "O4": "The visible evidence does not establish this"},
            "answer": "O2",
            "requiredEvidenceAll": ["F2", "F4"],
        },
        {
            "questionId": "Q5",
            "stage": "adaptation",
            "question": f"The gauge reaches {trigger}, the latch opens, coolant enters, and the {chamber} is measured below {safe_temp} degrees. May the {spindle} rotate safely under the stated mechanism?",
            "options": {"O1": "Yes", "O2": "No", "O3": "Only if the maintenance code changes", "O4": "The visible evidence does not establish this"},
            "answer": "O1",
            "requiredEvidenceAll": ["F4"],
        },
        {
            "questionId": "Q6",
            "stage": "adaptation",
            "question": f"The gauge reaches {trigger} and the latch opens, but coolant fails to enter and the {chamber} stays above {safe_temp} degrees. May the {spindle} rotate safely?",
            "options": {"O1": "Yes", "O2": "No", "O3": "The gauge alone makes it safe", "O4": "The visible evidence does not establish this"},
            "answer": "O2",
            "requiredEvidenceAll": ["F3", "F4"],
        },
    ]
    return {
        "mechanismId": mechanism_id,
        "seedDigest": seed_commitment(seed),
        "entities": {"gauge": gauge, "latch": latch, "chamber": chamber, "spindle": spindle, "trigger": trigger, "safeTemp": safe_temp},
        "facts": facts,
        "orders": orders,
        "questions": questions,
    }


def _manifest(mechanism: Mapping[str, Any], *, experiment_id: str, assignment_salt: str) -> dict[str, Any]:
    facts = mechanism["facts"]
    variants = []
    for variant in VARIANTS:
        variants.append(
            {
                "variantId": variant,
                "probability": 1 / 3,
                "title": f"Mechanism {mechanism['mechanismId']}",
                "sections": [
                    {"evidenceId": evidence_id, "heading": facts[evidence_id]["heading"], "text": facts[evidence_id]["text"]}
                    for evidence_id in mechanism["orders"][variant]
                ],
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.web.r6-encounter-manifest",
        "experimentId": experiment_id,
        "assignmentSalt": assignment_salt,
        "encounter": {"mode": "initial-viewport-no-scroll", "viewport": {"width": 1080, "height": 1050}},
        "variants": variants,
    }


def build_visible_protocol(*, holdout_seed_commitment: str) -> dict[str, Any]:
    visible_specs = [
        ("A", "r6c-visible-mechanism-a-20260811-v1"),
        ("B", "r6c-visible-mechanism-b-20260811-v1"),
    ]
    mechanisms = [_mechanism(seed, mechanism_id) for mechanism_id, seed in visible_specs]
    protocol = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-visible-creative-alpha-protocol",
        "experimentId": "experiment:studio:r6c:grounded-reveal-order",
        "hypothesis": "For an initial no-scroll browser encounter, presenting a grounded causal chain in causal order improves Agent-observer adaptation consequence relative to the same facts in a preregistered fragmented order.",
        "observerClass": "deepseek-flash-agent-observer",
        "encounter": {"surface": "ordivon-web-local-r6", "mode": "initial-viewport-no-scroll", "viewport": {"width": 1080, "height": 1050}},
        "primaryContrast": {"treatment": PRIMARY_TREATMENT, "control": PRIMARY_CONTROL},
        "outcomes": [
            {"outcomeId": "adaptation-accuracy", "role": "primary"},
            {"outcomeId": "grounding-validity", "role": "guardrail", "minimum": 0.95},
            {"outcomeId": "unsupported-assertion-rate", "role": "guardrail", "maximum": 0.02},
            {"outcomeId": "perception-accuracy", "role": "secondary"},
            {"outcomeId": "comprehension-accuracy", "role": "secondary"},
            {"outcomeId": "evidence-delayed-adaptation", "role": "exploratory"},
        ],
        "replicatesPerEncounter": 8,
        "promotionLaw": "Freeze the explicit-chain versus fragmented contrast before holdout reveal. Visible evidence is candidate-supporting only when adaptation delta > 0 and both grounding guardrails pass. Pristine content holdout must independently preserve a positive adaptation delta before any artifact-OOS promotion.",
        "holdout": {"status": "sealed", "seedCommitment": holdout_seed_commitment, "mechanismId": "C"},
        "mechanisms": [
            {
                "mechanismId": item["mechanismId"],
                "seedDigest": item["seedDigest"],
                "manifest": _manifest(item, experiment_id=f"experiment:web:r6c:mechanism-{item['mechanismId'].lower()}", assignment_salt=f"r6c-{item['mechanismId']}-assignment-20260811-v1"),
                "oracle": {"questions": item["questions"], "entities": item["entities"]},
            }
            for item in mechanisms
        ],
    }
    protocol["protocolDigest"] = canonical_digest(protocol)
    return protocol


def build_holdout_protocol(*, holdout_seed: str, expected_commitment: str, visible_selection: Mapping[str, Any]) -> dict[str, Any]:
    if seed_commitment(holdout_seed) != expected_commitment:
        raise ValueError("holdout seed does not satisfy visible protocol commitment")
    if visible_selection.get("contrast") != {"treatment": PRIMARY_TREATMENT, "control": PRIMARY_CONTROL}:
        raise ValueError("visible selection changed the preregistered contrast")
    mechanism = _mechanism(holdout_seed, "C")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-content-holdout-protocol",
        "experimentId": "experiment:studio:r6d:content-oos",
        "sourceVisibleScoreDigest": visible_selection.get("sourceScoreDigest"),
        "sourceSelectionDigest": visible_selection.get("selectionDigest"),
        "seedCommitment": expected_commitment,
        "mechanismId": "C",
        "contrast": dict(visible_selection["contrast"]),
        "manifest": _manifest(mechanism, experiment_id="experiment:web:r6d:mechanism-c-holdout", assignment_salt="r6d-C-assignment-20260811-v1"),
        "oracle": {"questions": mechanism["questions"], "entities": mechanism["entities"]},
        "oosScope": {"artifactContent": "pristine-sealed", "observer": "same-provider-class", "encounter": "same-web-initial-viewport", "time": "same-session", "medium": "same-web"},
    }
    result["holdoutProtocolDigest"] = canonical_digest(result)
    return result


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
    receipts = {str(receipt["experimentId"]).rsplit("-", 1)[-1].upper(): receipt for receipt in web_receipts}
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


def _score_task(task: Mapping[str, Any], observations: Sequence[Mapping[str, Any]], oracle: Mapping[str, Any]) -> dict[str, Any]:
    available = {item["evidenceId"] for item in task["userPayload"]["artifactEvidence"]}
    answer_oracle = oracle["answers"]
    stages = oracle["stages"]
    required = oracle["requiredEvidenceAll"]
    per_stage: dict[str, list[float]] = defaultdict(list)
    accuracies: list[float] = []
    groundings: list[float] = []
    unsupported: list[float] = []
    abstentions: list[float] = []
    for observation in observations:
        result = observation.get("result")
        answers = result.get("answers") if isinstance(result, dict) else None
        by_q = {item.get("questionId"): item for item in answers} if isinstance(answers, list) else {}
        for question_id, target in answer_oracle.items():
            item = by_q.get(question_id, {})
            option = item.get("optionId")
            refs = item.get("evidenceIds") if isinstance(item.get("evidenceIds"), list) else []
            accuracy = float(option == target)
            accuracies.append(accuracy)
            per_stage[stages[question_id]].append(accuracy)
            substantive = option != ABSTAIN_OPTION
            valid_refs = substantive and bool(refs) and all(ref in available for ref in refs)
            required_present = set(required[question_id]).issubset(set(refs))
            grounding = float((not substantive and not refs) or (valid_refs and required_present))
            groundings.append(grounding)
            unsupported.append(float(substantive and not grounding))
            abstentions.append(float(not substantive))
    if not accuracies:
        raise ValueError(f"no observations for {task['taskId']}")
    mean = lambda values: sum(values) / len(values) if values else 0.0
    return {
        "replicates": len(observations),
        "availableEvidenceIds": sorted(available),
        "meanAccuracy": mean(accuracies),
        "perStageAccuracy": {stage: mean(values) for stage, values in sorted(per_stage.items())},
        "groundingValidity": mean(groundings),
        "unsupportedAssertionRate": mean(unsupported),
        "abstentionRate": mean(abstentions),
    }


def score_observer_receipt(*, bundle: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    if canonical_digest({key: value for key, value in bundle.items() if key != "bundleDigest"}) != bundle.get("bundleDigest"):
        raise ValueError("observer bundle digest mismatch")
    tasks = {task["taskId"]: task for task in bundle["tasks"]}
    observations_by_task: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in receipt.get("results", []):
        if isinstance(item, dict) and item.get("taskId") in tasks:
            observations_by_task[str(item["taskId"])].append(item)
    task_scores = {}
    variant_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task_id, task in tasks.items():
        score = _score_task(task, observations_by_task[task_id], bundle["oracle"][task_id])
        task_scores[task_id] = score
        variant = task_id.rsplit(":", 1)[-1]
        variant_rows[variant].append(score)
    mean = lambda values: sum(values) / len(values) if values else 0.0
    variant_scores = {}
    for variant, rows in variant_rows.items():
        variant_scores[variant] = {
            "adaptationAccuracy": mean([row["perStageAccuracy"].get("adaptation", 0.0) for row in rows]),
            "comprehensionAccuracy": mean([row["perStageAccuracy"].get("comprehension", 0.0) for row in rows]),
            "perceptionAccuracy": mean([row["perStageAccuracy"].get("perception", 0.0) for row in rows]),
            "groundingValidity": mean([row["groundingValidity"] for row in rows]),
            "unsupportedAssertionRate": mean([row["unsupportedAssertionRate"] for row in rows]),
            "abstentionRate": mean([row["abstentionRate"] for row in rows]),
        }
    treatment = variant_scores[PRIMARY_TREATMENT]
    control = variant_scores[PRIMARY_CONTROL]
    delta = treatment["adaptationAccuracy"] - control["adaptationAccuracy"]
    score = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-creative-alpha-observer-score",
        "bundleDigest": bundle["bundleDigest"],
        "taskScores": task_scores,
        "variantScores": variant_scores,
        "primaryContrast": {
            "treatment": PRIMARY_TREATMENT,
            "control": PRIMARY_CONTROL,
            "adaptationAccuracyDelta": delta,
        },
        "guardrails": {
            "treatmentGroundingPass": treatment["groundingValidity"] >= 0.95,
            "treatmentUnsupportedAssertionPass": treatment["unsupportedAssertionRate"] <= 0.02,
        },
        "interpretationBoundary": "This score measures consequence for the declared Agent observer under initial-viewport evidence. It neither estimates human response nor establishes universal creative quality.",
    }
    score["scoreDigest"] = canonical_digest(score)
    return score


def freeze_visible_contrast(score: Mapping[str, Any]) -> dict[str, Any]:
    primary = score["primaryContrast"]
    guardrails = score["guardrails"]
    supported = float(primary["adaptationAccuracyDelta"]) > 0 and all(bool(value) for value in guardrails.values())
    selection = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-visible-contrast-freeze",
        "sourceScoreDigest": score["scoreDigest"],
        "contrast": {"treatment": PRIMARY_TREATMENT, "control": PRIMARY_CONTROL},
        "visibleCandidateSupported": supported,
        "visibleAdaptationDelta": primary["adaptationAccuracyDelta"],
        "holdoutLaw": "The treatment/control identity is now frozen. Holdout content may measure this contrast but may not change which contrast was selected.",
    }
    selection["selectionDigest"] = canonical_digest(selection)
    return selection


def score_content_oos(*, visible_selection: Mapping[str, Any], holdout_score: Mapping[str, Any]) -> dict[str, Any]:
    delta = float(holdout_score["primaryContrast"]["adaptationAccuracyDelta"])
    treatment = holdout_score["variantScores"][PRIMARY_TREATMENT]
    independent_support = delta > 0 and treatment["groundingValidity"] >= 0.95 and treatment["unsupportedAssertionRate"] <= 0.02
    dual_support = bool(visible_selection["visibleCandidateSupported"]) and independent_support
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-content-oos-score",
        "visibleSelectionDigest": visible_selection["selectionDigest"],
        "holdoutScoreDigest": holdout_score["scoreDigest"],
        "contrast": dict(visible_selection["contrast"]),
        "visibleAdaptationDelta": visible_selection["visibleAdaptationDelta"],
        "holdoutAdaptationDelta": delta,
        "holdoutIndependentSupport": independent_support,
        "artifactOOSPromotionSupport": dual_support,
        "oosScope": {"artifactContent": "tested-pristine", "observer": "not-oos", "encounter": "not-oos", "time": "not-oos", "medium": "not-oos"},
        "decisionLaw": "A holdout cannot rescue a visible contrast that failed its own preregistered evidence gate. Artifact-OOS support requires both visible candidate support and independent positive holdout support.",
    }
    result["oosScoreDigest"] = canonical_digest(result)
    return result



def _replicate_stage_accuracy(*, bundle: Mapping[str, Any], receipt: Mapping[str, Any], variant: str, stage: str) -> list[float]:
    oracle = bundle["oracle"]
    task_ids = [task["taskId"] for task in bundle["tasks"] if task["taskId"].rsplit(":", 1)[-1] == variant]
    values: list[float] = []
    for task_id in task_ids:
        task_oracle = oracle[task_id]
        target_questions = [qid for qid, qstage in task_oracle["stages"].items() if qstage == stage]
        rows = [item for item in receipt.get("results", []) if item.get("taskId") == task_id]
        for row in rows:
            result = row.get("result", {})
            answers = result.get("answers", []) if isinstance(result, dict) else []
            by_q = {item.get("questionId"): item.get("optionId") for item in answers if isinstance(item, dict)}
            if not target_questions:
                continue
            values.append(sum(by_q.get(qid) == task_oracle["answers"][qid] for qid in target_questions) / len(target_questions))
    if not values:
        raise ValueError(f"no replicate-level {stage} observations for {variant}")
    return values


def descriptive_contrast_uncertainty(
    *,
    visible_bundle: Mapping[str, Any],
    visible_receipt: Mapping[str, Any],
    holdout_bundle: Mapping[str, Any],
    holdout_receipt: Mapping[str, Any],
    bootstrap_draws: int = 20_000,
    seed: str = "r6-descriptive-bootstrap-20260811-v1",
) -> dict[str, Any]:
    if bootstrap_draws < 1000:
        raise ValueError("bootstrap_draws must be >= 1000")
    rng = _rng(seed)

    def summarize(bundle: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
        treatment = _replicate_stage_accuracy(bundle=bundle, receipt=receipt, variant=PRIMARY_TREATMENT, stage="adaptation")
        control = _replicate_stage_accuracy(bundle=bundle, receipt=receipt, variant=PRIMARY_CONTROL, stage="adaptation")
        observed = sum(treatment) / len(treatment) - sum(control) / len(control)
        draws: list[float] = []
        for _ in range(bootstrap_draws):
            sampled_treatment = [treatment[rng.randrange(len(treatment))] for _ in treatment]
            sampled_control = [control[rng.randrange(len(control))] for _ in control]
            draws.append(sum(sampled_treatment) / len(sampled_treatment) - sum(sampled_control) / len(sampled_control))
        draws.sort()
        def q(frac: float) -> float:
            pos = frac * (len(draws) - 1)
            low = int(pos); high = min(low + 1, len(draws) - 1); weight = pos - low
            return draws[low] * (1 - weight) + draws[high] * weight
        return {
            "treatmentReplicateCount": len(treatment),
            "controlReplicateCount": len(control),
            "treatmentReplicateAccuracies": treatment,
            "controlReplicateAccuracies": control,
            "observedAdaptationAccuracyDelta": observed,
            "bootstrap95PercentInterval": [q(0.025), q(0.975)],
            "bootstrapProbabilityDeltaPositive": sum(value > 0 for value in draws) / len(draws),
        }

    visible = summarize(visible_bundle, visible_receipt)
    holdout = summarize(holdout_bundle, holdout_receipt)
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-descriptive-contrast-uncertainty",
        "bootstrapDraws": bootstrap_draws,
        "bootstrapSeedDigest": seed_commitment(seed),
        "visible": visible,
        "pristineContentHoldout": holdout,
        "effectShrinkage": holdout["observedAdaptationAccuracyDelta"] - visible["observedAdaptationAccuracyDelta"],
        "interpretationBoundary": (
            "This is a post-freeze descriptive nonparametric bootstrap over Provider replicate-level adaptation accuracy. "
            "It does not alter the preregistered visible or holdout decision law, does not make Provider replicates equivalent to independent humans, "
            "and does not establish population-level causal confidence intervals."
        ),
    }
    result["uncertaintyDigest"] = canonical_digest(result)
    return result

def creative_portfolio_counterfactual(*, visible_score: Mapping[str, Any], holdout_score: Mapping[str, Any]) -> dict[str, Any]:
    measured = {
        variant: (
            float(visible_score["variantScores"][variant]["adaptationAccuracy"]) * 2
            + float(holdout_score["variantScores"][variant]["adaptationAccuracy"])
        ) / 3
        for variant in VARIANTS
    }
    scenarios = {
        "already-explicit-heavy": {"explicit-chain": 0.80, "fragmented": 0.10, "evidence-delayed": 0.10},
        "fragmented-heavy": {"explicit-chain": 0.10, "fragmented": 0.80, "evidence-delayed": 0.10},
        "balanced": {variant: 1 / 3 for variant in VARIANTS},
    }
    candidate = PRIMARY_TREATMENT
    allocation = 0.20
    rows = {}
    for scenario, weights in scenarios.items():
        current_accuracy = sum(weights[variant] * measured[variant] for variant in VARIANTS)
        target = {variant: (1 - allocation) * weights[variant] for variant in VARIANTS}
        target[candidate] += allocation
        target_accuracy = sum(target[variant] * measured[variant] for variant in VARIANTS)
        current_concentration = sum(weight * weight for weight in weights.values())
        target_concentration = sum(weight * weight for weight in target.values())
        rows[scenario] = {
            "currentWeights": weights,
            "targetWeights": target,
            "candidateAllocation": allocation,
            "meanAdaptationAccuracyDelta": target_accuracy - current_accuracy,
            "expressionConcentrationDelta": target_concentration - current_concentration,
            "interpretation": "The same measured candidate is evaluated as a funded reallocation of creative-program attention, not as a standalone quality score.",
        }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.r6-creative-program-portfolio-counterfactual",
        "measuredVariantAdaptationAccuracy": measured,
        "candidate": candidate,
        "scenarios": rows,
        "boundary": "Expression concentration is a program-composition diagnostic, not a utility function. This counterfactual demonstrates context dependence of marginal program contribution; it is not a human audience portfolio optimization claim.",
    }
    result["portfolioDigest"] = canonical_digest(result)
    return result
