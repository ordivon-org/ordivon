#!/usr/bin/env python3
"""H-9B Dogfood Runner — executes 10 real/realistic Finance DecisionIntake runs."""
import json
import sys
import time
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
            return {"_error": e.code, "_body": e.read().decode()[:500]}

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

runs = []

# --- Run 2: Over-leveraged position → REJECT ---
print("=== RUN 2: Over-leveraged position ===")
r2 = intake({
    "symbol": "ETHUSDT", "timeframe": "15m", "direction": "short",
    "thesis": "ETH looks weak, full port short",
    "stop_loss": "50%",
    "max_loss_usdt": 8000,
    "position_size_usdt": 100000,
    "risk_unit_usdt": 2000,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "excited", "confidence": 0.85,
})
r2_gov = govern(r2["id"]) if "id" in r2 else {}
runs.append({"tag": "Run 2", "intake": r2, "governance": r2_gov})
print(f"  intake_id={r2.get('id')} → governance={r2_gov.get('governance_decision')}")
print(f"  reasons={r2_gov.get('governance_reasons')}")

# --- Run 3: Ambiguous/market-dependent → ESCALATE ---
print("\n=== RUN 3: Ambiguous thesis ===")
r3 = intake({
    "symbol": "SOLUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "Complex confluence: S/R flip + funding reset + dev conference next week",
    "stop_loss": "8%",
    "max_loss_usdt": 1500,
    "position_size_usdt": 15000,
    "risk_unit_usdt": 1500,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.55,
})
r3_gov = govern(r3["id"]) if "id" in r3 else {}
runs.append({"tag": "Run 3", "intake": r3, "governance": r3_gov})
print(f"  intake_id={r3.get('id')} → governance={r3_gov.get('governance_decision')}")
print(f"  reasons={r3_gov.get('governance_reasons')}")

# --- Run 4: Meme coin chase → ESCALATE ---
print("\n=== RUN 4: Meme coin chase ===")
r4 = intake({
    "symbol": "DOGEUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "Meme coin momentum + Elon tweet catalyst",
    "stop_loss": "0.5%",
    "max_loss_usdt": 500,
    "position_size_usdt": 20000,
    "risk_unit_usdt": 1000,
    "is_revenge_trade": False, "is_chasing": True,
    "emotional_state": "excited", "confidence": 0.9,
})
r4_gov = govern(r4["id"]) if "id" in r4 else {}
runs.append({"tag": "Run 4", "intake": r4, "governance": r4_gov})
print(f"  intake_id={r4.get('id')} → governance={r4_gov.get('governance_decision')}")
print(f"  reasons={r4_gov.get('governance_reasons')}")

# --- Run 5: Clean swing trade → EXECUTE → FULL CHAIN ---
print("\n=== RUN 5: Clean swing trade → FULL CHAIN ===")
r5 = intake({
    "symbol": "BTCUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "BTC holding above 200 EMA on 4h, volume confirming, targeting range high",
    "stop_loss": "2%",
    "max_loss_usdt": 400,
    "position_size_usdt": 2000,
    "risk_unit_usdt": 200,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.7,
})
r5_gov = govern(r5["id"]) if "id" in r5 else {}
r5_plan = {}
r5_outcome = {}
r5_review = {}
if r5_gov.get("governance_decision") == "execute":
    r5_plan = plan(r5["id"])
    if "execution_receipt_id" in r5_plan:
        r5_outcome = outcome(r5["id"], {
            "execution_receipt_id": r5_plan["execution_receipt_id"],
            "observed_outcome": "Price touched target +4.5% then retraced. Exited at +3.8%.",
            "verdict": "validated",
            "variance_summary": "Plan anticipated +4% target. Actual exit +3.8%, within tolerance.",
            "plan_followed": True,
        })
        if "outcome_id" in r5_outcome:
            r5_review = submit_review({
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "BTC reaches 4h range high, exit at +4%",
                "actual_outcome": "BTC reached +4.5%, exited at +3.8%",
                "deviation": "Early exit by 0.7%, within plan tolerance",
                "mistake_tags": "plan_discipline, partial_execution",
                "lessons": [{"lesson_text": "Trust the plan: early exit cost 0.7% but preserved capital on retrace."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome",
                "outcome_ref_id": r5_outcome["outcome_id"],
            })
runs.append({"tag": "Run 5", "intake": r5, "governance": r5_gov, "plan": r5_plan, "outcome": r5_outcome, "review": r5_review})
print(f"  intake_id={r5.get('id')} → governance={r5_gov.get('governance_decision')}")
print(f"  plan_receipt={r5_plan.get('execution_receipt_id')}")
print(f"  outcome={r5_outcome.get('outcome_id')}")
print(f"  review={r5_review.get('id')}")

time.sleep(0.2)

# --- Run 6: Day trade with tight stop → EXECUTE → LOSS → FULL CHAIN ---
print("\n=== RUN 6: Day trade → LOSS → FULL CHAIN ===")
r6 = intake({
    "symbol": "ETHUSDT", "timeframe": "1h", "direction": "short",
    "thesis": "ETH rejected from resistance, bearish diverg on 1h RSI",
    "stop_loss": "1.5%",
    "max_loss_usdt": 300,
    "position_size_usdt": 1500,
    "risk_unit_usdt": 150,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.65,
})
r6_gov = govern(r6["id"]) if "id" in r6 else {}
r6_plan = {}
r6_outcome = {}
r6_review = {}
if r6_gov.get("governance_decision") == "execute":
    r6_plan = plan(r6["id"])
    if "execution_receipt_id" in r6_plan:
        r6_outcome = outcome(r6["id"], {
            "execution_receipt_id": r6_plan["execution_receipt_id"],
            "observed_outcome": "ETH wicked stop loss by 0.3% then reversed. Full loss realized.",
            "verdict": "invalidated",
            "variance_summary": "Stop triggered within first hour. No chance to adjust.",
            "plan_followed": True,
        })
        if "outcome_id" in r6_outcome:
            r6_review = submit_review({
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "ETH drops 3-4% on bearish divergence",
                "actual_outcome": "Stop loss hit, -1.5% loss",
                "deviation": "Market wicked the stop, plan could not recover",
                "mistake_tags": "entry_timing, stop_placement",
                "lessons": [
                    {"lesson_text": "Stop loss was too tight for ETH 1h volatility — need wider buffer at resistance."},
                    {"lesson_text": "Wait for candle close before entering on divergences."},
                ],
                "new_rule_candidate": "Min stop distance must be 2x ATR for sub-4h timeframes",
                "outcome_ref_type": "finance_manual_outcome",
                "outcome_ref_id": r6_outcome["outcome_id"],
            })
runs.append({"tag": "Run 6", "intake": r6, "governance": r6_gov, "plan": r6_plan, "outcome": r6_outcome, "review": r6_review})
print(f"  intake_id={r6.get('id')} → governance={r6_gov.get('governance_decision')}")
print(f"  plan_receipt={r6_plan.get('execution_receipt_id')}")
print(f"  outcome={r6_outcome.get('outcome_id')}")
print(f"  review={r6_review.get('id')}")

time.sleep(0.2)

# --- Run 7: Conservative clear trade → EXECUTE → WIN → FULL CHAIN ---
print("\n=== RUN 7: Conservative clear trade → WIN → FULL CHAIN ===")
r7 = intake({
    "symbol": "LINKUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "LINK daily double bottom with volume confirmation, targeting 200 MA",
    "stop_loss": "5%",
    "max_loss_usdt": 250,
    "position_size_usdt": 2500,
    "risk_unit_usdt": 250,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.75,
})
r7_gov = govern(r7["id"]) if "id" in r7 else {}
r7_plan = {}
r7_outcome = {}
r7_review = {}
if r7_gov.get("governance_decision") == "execute":
    r7_plan = plan(r7["id"])
    if "execution_receipt_id" in r7_plan:
        r7_outcome = outcome(r7["id"], {
            "execution_receipt_id": r7_plan["execution_receipt_id"],
            "observed_outcome": "LINK consolidated for 2 days then broke up. Exited at +7.2%.",
            "verdict": "validated",
            "variance_summary": "Patience paid off. Better than expected exit.",
            "plan_followed": True,
        })
        if "outcome_id" in r7_outcome:
            r7_review = submit_review({
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "LINK rallies to 200 MA, exit at +8-10%",
                "actual_outcome": "Exited +7.2% at 200 MA touch",
                "deviation": "Exit within plan range, slight underperformance vs ideal",
                "mistake_tags": "plan_execution",
                "lessons": [{"lesson_text": "Daily timeframe double bottoms are reliable when volume-confirmed."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome",
                "outcome_ref_id": r7_outcome["outcome_id"],
            })
runs.append({"tag": "Run 7", "intake": r7, "governance": r7_gov, "plan": r7_plan, "outcome": r7_outcome, "review": r7_review})
print(f"  intake_id={r7.get('id')} → governance={r7_gov.get('governance_decision')}")
print(f"  plan_receipt={r7_plan.get('execution_receipt_id')}")
print(f"  outcome={r7_outcome.get('outcome_id')}")
print(f"  review={r7_review.get('id')}")

time.sleep(0.2)

# --- Run 8: Emotional FOMO chase → REJECT ---
print("\n=== RUN 8: Emotional FOMO chase ===")
r8 = intake({
    "symbol": "PEPEUSDT", "timeframe": "5m", "direction": "long",
    "thesis": "PEPE pumping 40%, FOMO is real, I need in NOW",
    "stop_loss": "0.3%",
    "max_loss_usdt": 2000,
    "position_size_usdt": 5000,
    "risk_unit_usdt": 500,
    "is_revenge_trade": False, "is_chasing": True,
    "emotional_state": "excited", "confidence": 0.95,
})
r8_gov = govern(r8["id"]) if "id" in r8 else {}
runs.append({"tag": "Run 8", "intake": r8, "governance": r8_gov})
print(f"  intake_id={r8.get('id')} → governance={r8_gov.get('governance_decision')}")
print(f"  reasons={r8_gov.get('governance_reasons')}")

time.sleep(0.2)

# --- Run 9: Moderate trade → EXECUTE but FAKEOUT LOSS → FULL CHAIN ---
print("\n=== RUN 9: Moderate trade → FAKEOUT LOSS → FULL CHAIN ===")
r9 = intake({
    "symbol": "AVAXUSDT", "timeframe": "4h", "direction": "short",
    "thesis": "AVAX breakdown below support after fakeout, volume spike confirming",
    "stop_loss": "3%",
    "max_loss_usdt": 300,
    "position_size_usdt": 1500,
    "risk_unit_usdt": 150,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.6,
})
r9_gov = govern(r9["id"]) if "id" in r9 else {}
r9_plan = {}
r9_outcome = {}
r9_review = {}
if r9_gov.get("governance_decision") == "execute":
    r9_plan = plan(r9["id"])
    if "execution_receipt_id" in r9_plan:
        r9_outcome = outcome(r9["id"], {
            "execution_receipt_id": r9_plan["execution_receipt_id"],
            "observed_outcome": "AVAX bounced off support, never broke down. Full stop loss hit.",
            "verdict": "invalidated",
            "variance_summary": "Fakeout - what looked like a breakdown was a liquidity grab.",
            "plan_followed": True,
        })
        if "outcome_id" in r9_outcome:
            r9_review = submit_review({
                "recommendation_id": None,
                "review_type": "recommendation_postmortem",
                "expected_outcome": "AVAX breaks support, drops 5-6%",
                "actual_outcome": "Fakeout, reversed and hit stop loss",
                "deviation": "Entry signal was a trap - market had different intent",
                "mistake_tags": "false_breakdown, entry_timing",
                "lessons": [
                    {"lesson_text": "Volume spike on breakdown can be a liquidity grab - wait for retest."},
                    {"lesson_text": "4h closes are more reliable than intra-4h price action."},
                ],
                "new_rule_candidate": "Require candle close beyond support before entering breakdown trades",
                "outcome_ref_type": "finance_manual_outcome",
                "outcome_ref_id": r9_outcome["outcome_id"],
            })
runs.append({"tag": "Run 9", "intake": r9, "governance": r9_gov, "plan": r9_plan, "outcome": r9_outcome, "review": r9_review})
print(f"  intake_id={r9.get('id')} → governance={r9_gov.get('governance_decision')}")
print(f"  plan_receipt={r9_plan.get('execution_receipt_id')}")
print(f"  outcome={r9_outcome.get('outcome_id')}")
print(f"  review={r9_review.get('id')}")

time.sleep(0.2)

# --- Run 10: Missing thesis → ESCALATE (or execute if borderline) ---
print("\n=== RUN 10: Missing thesis ===")
r10 = intake({
    "symbol": "BNBUSDT", "timeframe": "1h", "direction": "long",
    "thesis": "No specific thesis, just feels right",
    "stop_loss": "2%",
    "max_loss_usdt": 400,
    "position_size_usdt": 2000,
    "risk_unit_usdt": 200,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.6,
})
r10_gov = govern(r10["id"]) if "id" in r10 else {}
runs.append({"tag": "Run 10", "intake": r10, "governance": r10_gov})
print(f"  intake_id={r10.get('id')} → governance={r10_gov.get('governance_decision')}")
print(f"  reasons={r10_gov.get('governance_reasons')}")

# Complete reviews for full-chain runs
print("\n=== COMPLETING REVIEWS ===")
for run in runs:
    rev = run.get("review", {})
    rev_id = rev.get("id")
    if rev_id:
        actual = rev.get("actual_outcome", "")
        # Determine verdict based on outcome text and actual_outcome
        actual_text = (rev.get("actual_outcome", "") + " " + actual).lower()
        if any(w in actual_text for w in ("loss", "hit stop", "reversed", "fakeout", "bounced", "wicked")):
            verdict = "invalidated"
        elif actual_text.strip():
            verdict = "validated"
        else:
            verdict = "inconclusive"
        comp = complete_review(rev_id, {
            "observed_outcome": actual,
            "verdict": verdict,
            "variance_summary": rev.get("deviation", ""),
            "cause_tags": rev.get("mistake_tags", "").split(", ") if rev.get("mistake_tags") else [],
            "lessons": [l["lesson_text"] for l in rev.get("lessons", [])],
            "followup_actions": [rev.get("new_rule_candidate")] if rev.get("new_rule_candidate") else [],
            "require_approval": False,
        })
        run["review_completed"] = comp
        print(f"  Review {rev_id} completed: status={comp.get('status')}, lessons={comp.get('lessons_created')}")

# ============================================================
# OUTPUT SUMMARY
# ============================================================
print("\n\n========== FINAL SUMMARY ==========")
for i, run in enumerate(runs, 1):
    tag = run["tag"]
    intake_id = run["intake"].get("id", "???")
    gov_dec = run["governance"].get("governance_decision", "???")
    reasons = run["governance"].get("governance_reasons", [])
    plan_id = run.get("plan", {}).get("execution_receipt_id", "—")
    outcome_id = run.get("outcome", {}).get("outcome_id", "—")
    review_id = run.get("review", {}).get("id", "—")
    rev_completed = run.get("review_completed", {}).get("status", "—")
    print(f"{tag}: intake={intake_id} → gov={gov_dec} | plan={plan_id} | outcome={outcome_id} | review={review_id} (status={rev_completed})")
    if reasons:
        for r in reasons:
            print(f"       reason: {r}")

# Export as JSON for evidence report
print("\n\n--- RAW JSON ---")
print(json.dumps(runs, indent=2, default=str))
