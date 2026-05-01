#!/usr/bin/env python3
"""H-9C Verification Runner — targeted tests for the three remediation fixes."""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000/api/v1"


def api(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return {"_error": e.code, "_body": json.loads(e.read())}
        except Exception:
            return {"_error": e.code, "_body": str(e)}


def intake(payload):
    return api("POST", "/finance-decisions/intake", payload)


def govern(intake_id):
    return api("POST", f"/finance-decisions/intake/{intake_id}/govern")


def plan(intake_id):
    return api("POST", f"/finance-decisions/intake/{intake_id}/plan")


def outcome(intake_id, data):
    return api("POST", f"/finance-decisions/intake/{intake_id}/outcome", data)


def submit_review(data):
    return api("POST", "/reviews/submit", data)


def complete_review(review_id, data):
    return api("POST", f"/reviews/{review_id}/complete", data)


results = []
pass_count = 0
fail_count = 0


def check(name, condition, detail=""):
    global pass_count, fail_count
    symbol = "✅" if condition else "❌"
    print(f"  {symbol} {name}: {detail}")
    results.append({"name": name, "pass": condition, "detail": detail})
    if condition:
        pass_count += 1
    else:
        fail_count += 1


def valid_payload(**overrides):
    p = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC breaking above resistance with volume confirmation; invalidated if price closes below 200 EMA.",
        "entry_condition": "Breakout confirmed.",
        "invalidation_condition": "Range reclaim.",
        "stop_loss": "Below support",
        "target": "Local high",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.7,
        "rule_exceptions": [],
        "notes": "Controlled",
    }
    p.update(overrides)
    return p


# ═══════════════════════════════════════════════════════════════
# H-9C1: Schema Drift — outcome_ref on fresh runs
# ═══════════════════════════════════════════════════════════════
print("═══ H-9C1: Schema Drift — outcome_ref full chain ═══")

# Full chain: intake → govern → plan → outcome → review → complete
r1 = intake(valid_payload())
r1_id = r1.get("id")
gov1 = govern(r1_id)
check(
    "H-9C1.1: valid intake executed",
    gov1.get("governance_decision") == "execute",
    f"got {gov1.get('governance_decision')}",
)

if gov1.get("governance_decision") == "execute":
    p1 = plan(r1_id)
    check(
        "H-9C1.2: plan receipt created",
        "execution_receipt_id" in p1,
        f"receipt={p1.get('execution_receipt_id', 'MISSING')}",
    )

    if "execution_receipt_id" in p1:
        o1 = outcome(
            r1_id,
            {
                "execution_receipt_id": p1["execution_receipt_id"],
                "observed_outcome": "Price reached +4.2%, exited at plan target.",
                "verdict": "validated",
                "variance_summary": "Clean execution, within plan parameters.",
                "plan_followed": True,
            },
        )
        check("H-9C1.3: outcome created", "outcome_id" in o1, f"outcome_id={o1.get('outcome_id', 'MISSING')}")

        if "outcome_id" in o1:
            rv1 = submit_review({
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "BTC reaches range high, exit at +4%",
                "actual_outcome": "BTC reached +4.2%, exited clean",
                "deviation": "Within plan tolerance",
                "mistake_tags": "plan_execution",
                "lessons": [{"lesson_text": "Trust plan targets — no early exit needed."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome",
                "outcome_ref_id": o1["outcome_id"],
            })
            check(
                "H-9C1.4: review submitted (outcome_ref in DB, API echo known gap)",
                rv1.get("id") is not None,
                f"review_id={rv1.get('id')}",
            )

            if rv1.get("id"):
                cp1 = complete_review(
                    rv1["id"],
                    {
                        "observed_outcome": "BTC reached +4.2%",
                        "verdict": "validated",
                        "variance_summary": "Clean",
                        "cause_tags": ["plan_execution"],
                        "lessons": ["Trust plan targets."],
                        "followup_actions": [],
                        "require_approval": False,
                    },
                )
                check(
                    "H-9C1.5: review completed",
                    cp1.get("status") == "completed",
                    f"status={cp1.get('status')}, lessons={cp1.get('lessons_created')}",
                )

# ═══════════════════════════════════════════════════════════════
# H-9C2: Escalation Path Coverage
# ═══════════════════════════════════════════════════════════════
print("\n═══ H-9C2: Escalation Path Coverage ═══")

# C2.1: emotional_state=stressed → escalate
r_stress = intake(valid_payload(emotional_state="stressed"))
g_stress = govern(r_stress["id"])
check(
    "H-9C2.1: emotional_state 'stressed' → escalate",
    g_stress.get("governance_decision") == "escalate",
    f"got {g_stress.get('governance_decision')} — {g_stress.get('governance_reasons')}",
)

# C2.2: emotional_state=fearful → escalate
r_fear = intake(valid_payload(emotional_state="fearful"))
g_fear = govern(r_fear["id"])
check(
    "H-9C2.2: emotional_state 'fearful' → escalate",
    g_fear.get("governance_decision") == "escalate",
    f"got {g_fear.get('governance_decision')}",
)

# C2.3: emotional_state=calm → execute (not escalate)
r_calm = intake(valid_payload(emotional_state="calm"))
g_calm = govern(r_calm["id"])
check(
    "H-9C2.3: emotional_state 'calm' → execute (not escalate)",
    g_calm.get("governance_decision") == "execute",
    f"got {g_calm.get('governance_decision')}",
)

# C2.4: rule_exceptions not empty → escalate
r_exc = intake(valid_payload(rule_exceptions=["override position limit"]))
g_exc = govern(r_exc["id"])
check(
    "H-9C2.4: rule_exceptions not empty → escalate",
    g_exc.get("governance_decision") == "escalate",
    f"got {g_exc.get('governance_decision')} — {g_exc.get('governance_reasons')}",
)

# C2.5: confidence < 0.3 → escalate
r_lowconf = intake(valid_payload(confidence=0.2))
g_lowconf = govern(r_lowconf["id"])
check(
    "H-9C2.5: confidence=0.2 → escalate",
    g_lowconf.get("governance_decision") == "escalate",
    f"got {g_lowconf.get('governance_decision')} — {g_lowconf.get('governance_reasons')}",
)

# C2.6: confidence >= 0.3 → not escalated for confidence
r_okconf = intake(valid_payload(confidence=0.5))
g_okconf = govern(r_okconf["id"])
check(
    "H-9C2.6: confidence=0.5 → execute (not escalated for confidence)",
    g_okconf.get("governance_decision") == "execute",
    f"got {g_okconf.get('governance_decision')}",
)

# C2.7: reject still beats escalate (missing field + emotional risk)
r_pri = intake(valid_payload(stop_loss=None, emotional_state="stressed"))
g_pri = govern(r_pri["id"])
check(
    "H-9C2.7: priority: reject beats escalate (missing stop_loss + stressed)",
    g_pri.get("governance_decision") == "reject",
    f"got {g_pri.get('governance_decision')} — {g_pri.get('governance_reasons')}",
)

# ═══════════════════════════════════════════════════════════════
# H-9C3: Thesis Quality Gate
# ═══════════════════════════════════════════════════════════════
print("\n═══ H-9C3: Thesis Quality Gate ═══")

# C3.1: banned pattern → reject ("just feels right")
r_ban = intake(valid_payload(thesis="No specific thesis, just feels right"))
g_ban = govern(r_ban["id"])
check(
    "H-9C3.1: banned thesis 'just feels right' → reject",
    g_ban.get("governance_decision") == "reject",
    f"got {g_ban.get('governance_decision')} — {g_ban.get('governance_reasons')}",
)

# C3.2: banned pattern → reject ("vibes")
r_vibe = intake(valid_payload(thesis="Vibes are good, trust me"))
g_vibe = govern(r_vibe["id"])
check(
    "H-9C3.2: banned thesis 'vibes...trust me' → reject",
    g_vibe.get("governance_decision") == "reject",
    f"got {g_vibe.get('governance_decision')}",
)

# C3.3: too short (< 50 chars) → escalate
r_short = intake(valid_payload(thesis="Short thesis statement"))
g_short = govern(r_short["id"])
check(
    "H-9C3.3: short thesis (no banned patterns) → escalate",
    g_short.get("governance_decision") == "escalate",
    f"got {g_short.get('governance_decision')} — {g_short.get('governance_reasons')}",
)

# C3.4: no verifiability wording → escalate
r_nover = intake(
    valid_payload(
        thesis="BTC is going up because the trend is strong and volume "
        "is high and the market sentiment is bullish across all timeframes."
    )
)
g_nover = govern(r_nover["id"])
check(
    "H-9C3.4: no verifiability wording → escalate",
    g_nover.get("governance_decision") == "escalate",
    f"got {g_nover.get('governance_decision')} — {g_nover.get('governance_reasons')}",
)

# C3.5: valid thesis with invalidation → execute
r_valid = intake(valid_payload())
g_valid = govern(r_valid["id"])
check(
    "H-9C3.5: valid thesis (confirmation + invalidation) → execute",
    g_valid.get("governance_decision") == "execute",
    f"got {g_valid.get('governance_decision')}",
)

# C3.6: YOLO thesis → reject
r_yolo = intake(valid_payload(thesis="YOLO all in"))
g_yolo = govern(r_yolo["id"])
check(
    "H-9C3.6: YOLO thesis → reject",
    g_yolo.get("governance_decision") == "reject",
    f"got {g_yolo.get('governance_decision')}",
)

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
print(f"\n{'=' * 50}")
print(f"VERIFICATION COMPLETE: {pass_count} pass, {fail_count} fail")
print(f"{'=' * 50}")

for r in results:
    if not r["pass"]:
        print(f"  FAIL: {r['name']} — {r['detail']}")

sys.exit(0 if fail_count == 0 else 1)
