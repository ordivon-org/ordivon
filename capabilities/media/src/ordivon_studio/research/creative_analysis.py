"""Independent R6 Agent-observer score, holdout and uncertainty methods.

Scoring is grounded in bounded browser receipt evidence. Bootstrap and
portfolio results are descriptive, never population-level causal claims.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from .creative_protocol import PRIMARY_CONTROL, PRIMARY_TREATMENT, VARIANTS, _rng
from .grounded_contracts import canonical_digest
from .trial_registration import seed_commitment

ABSTAIN_OPTION = "O4"



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
