"""R6 controlled creative intervention and sealed-content protocol.

Contains only deterministic mechanism/manifest construction and the frozen
visible-vs-holdout contrast; no observer receipt or scoring authority.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping
from typing import Any

from .grounded_contracts import canonical_digest
from .trial_registration import seed_commitment

VARIANTS = ("explicit-chain", "fragmented", "evidence-delayed")
PRIMARY_TREATMENT = "explicit-chain"
PRIMARY_CONTROL = "fragmented"



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
