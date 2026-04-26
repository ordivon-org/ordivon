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

# ══════════════════════════════════════════════════════════════════════
# Wave 4: Extended Dogfood — 21 new runs (Runs 11-31)
# ══════════════════════════════════════════════════════════════════════

time.sleep(0.2)

# --- Run 11: MATIC range reclaim → EXECUTE → FULL CHAIN ---
print("\n=== RUN 11: MATIC range reclaim → FULL CHAIN ===")
r11 = intake({
    "symbol": "MATICUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "MATIC reclaiming range support with volume spike confirming accumulation; "
             "invalidated if price closes back below range low.",
    "stop_loss": "5%", "max_loss_usdt": 120, "position_size_usdt": 800,
    "risk_unit_usdt": 80, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.7,
})
r11_gov = govern(r11["id"]) if "id" in r11 else {}
r11_plan = {}; r11_outcome = {}; r11_review = {}
if r11_gov.get("governance_decision") == "execute":
    r11_plan = plan(r11["id"])
    if "execution_receipt_id" in r11_plan:
        r11_outcome = outcome(r11["id"], {
            "execution_receipt_id": r11_plan["execution_receipt_id"],
            "observed_outcome": "MATIC rallied +11% to range high, plan executed.",
            "verdict": "validated", "variance_summary": "Clean execution.",
            "plan_followed": True,
        })
        if "outcome_id" in r11_outcome:
            r11_review = submit_review({
                "recommendation_id": None, "review_type": "recommendation_postmortem",
                "expected_outcome": "MATIC reaches range high",
                "actual_outcome": "MATIC rallied +11%",
                "deviation": "Clean", "mistake_tags": "range_trading",
                "lessons": [{"lesson_text": "MATIC range reclaims with volume are reliable setups."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome", "outcome_ref_id": r11_outcome["outcome_id"],
            })
runs.append({"tag": "Run 11", "intake": r11, "governance": r11_gov, "plan": r11_plan, "outcome": r11_outcome, "review": r11_review})
print(f"  intake_id={r11.get('id')} → governance={r11_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 12: XRP extreme leverage → REJECT ---
print("\n=== RUN 12: XRP extreme leverage ===")
r12 = intake({
    "symbol": "XRPUSDT", "timeframe": "15m", "direction": "long",
    "thesis": "XRP looking strong, go big or go home",
    "stop_loss": "1%", "max_loss_usdt": 5000, "position_size_usdt": 50000,
    "risk_unit_usdt": 500, "is_revenge_trade": False, "is_chasing": True,
    "emotional_state": "excited", "confidence": 0.9,
})
r12_gov = govern(r12["id"]) if "id" in r12 else {}
runs.append({"tag": "Run 12", "intake": r12, "governance": r12_gov})
print(f"  → governance={r12_gov.get('governance_decision')}, reasons={r12_gov.get('governance_reasons')}")

time.sleep(0.2)

# --- Run 13: ARB anxious day trade → ESCALATE ---
print("\n=== RUN 13: ARB anxious day trade ===")
r13 = intake({
    "symbol": "ARBUSDT", "timeframe": "1h", "direction": "short",
    "thesis": "ARB breakdown below support with volume spike confirming distribution; "
             "invalidated if price closes back above support.",
    "stop_loss": "2%", "max_loss_usdt": 150, "position_size_usdt": 1000,
    "risk_unit_usdt": 100, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "anxious", "confidence": 0.45,
})
r13_gov = govern(r13["id"]) if "id" in r13 else {}
runs.append({"tag": "Run 13", "intake": r13, "governance": r13_gov})
print(f"  → governance={r13_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 14: OP borderline risk ratio (exactly at limit) → EXECUTE ---
print("\n=== RUN 14: OP borderline risk ratio ===")
r14 = intake({
    "symbol": "OPUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "OP holding above key S/R with higher lows pattern; invalidated if "
             "price closes below the most recent higher low.",
    "stop_loss": "4%", "max_loss_usdt": 200, "position_size_usdt": 1000,
    "risk_unit_usdt": 100, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.6,
})
r14_gov = govern(r14["id"]) if "id" in r14 else {}
runs.append({"tag": "Run 14", "intake": r14, "governance": r14_gov})
print(f"  → governance={r14_gov.get('governance_decision')} (max_loss/risk_unit=2.0, position/risk_unit=10.0)")

time.sleep(0.2)

# --- Run 15: BTC weekly support → EXECUTE → FULL CHAIN ---
print("\n=== RUN 15: BTC weekly support → FULL CHAIN ===")
r15 = intake({
    "symbol": "BTCUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "BTC holding above weekly 50 MA with bullish MACD crossover; "
             "invalidated if price closes below weekly 50 MA.",
    "stop_loss": "3%", "max_loss_usdt": 600, "position_size_usdt": 4000,
    "risk_unit_usdt": 400, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.75,
})
r15_gov = govern(r15["id"]) if "id" in r15 else {}
r15_plan = {}; r15_outcome = {}; r15_review = {}
if r15_gov.get("governance_decision") == "execute":
    r15_plan = plan(r15["id"])
    if "execution_receipt_id" in r15_plan:
        r15_outcome = outcome(r15["id"], {
            "execution_receipt_id": r15_plan["execution_receipt_id"],
            "observed_outcome": "BTC rallied +5.2% above weekly resistance, plan validated.",
            "verdict": "validated", "variance_summary": "Clean execution.",
            "plan_followed": True,
        })
        if "outcome_id" in r15_outcome:
            r15_review = submit_review({
                "recommendation_id": None, "review_type": "recommendation_postmortem",
                "expected_outcome": "BTC rallies from weekly support",
                "actual_outcome": "BTC rallied +5.2%",
                "deviation": "Clean", "mistake_tags": "trend_following",
                "lessons": [{"lesson_text": "Weekly 50 MA retests are high-probability entries on BTC."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome", "outcome_ref_id": r15_outcome["outcome_id"],
            })
runs.append({"tag": "Run 15", "intake": r15, "governance": r15_gov, "plan": r15_plan, "outcome": r15_outcome, "review": r15_review})
print(f"  intake_id={r15.get('id')} → governance={r15_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 16: PEPE 1m scalp → REJECT (sub-5m + chasing) ---
print("\n=== RUN 16: PEPE 1m scalp ===")
r16 = intake({
    "symbol": "PEPEUSDT", "timeframe": "1m", "direction": "long",
    "thesis": "PEPE just pumped 200%, still going",
    "stop_loss": "0.1%", "max_loss_usdt": 2000, "position_size_usdt": 8000,
    "risk_unit_usdt": 500, "is_revenge_trade": False, "is_chasing": True,
    "emotional_state": "excited", "confidence": 0.95,
})
r16_gov = govern(r16["id"]) if "id" in r16 else {}
runs.append({"tag": "Run 16", "intake": r16, "governance": r16_gov})
print(f"  → governance={r16_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 17: SOL fearful short → ESCALATE ---
print("\n=== RUN 17: SOL fearful short ===")
r17 = intake({
    "symbol": "SOLUSDT", "timeframe": "4h", "direction": "short",
    "thesis": "SOL breaking down with bear flag pattern; invalidated if price "
             "closes back above flag resistance.",
    "stop_loss": "3%", "max_loss_usdt": 300, "position_size_usdt": 2000,
    "risk_unit_usdt": 200, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "fearful", "confidence": 0.4,
})
r17_gov = govern(r17["id"]) if "id" in r17 else {}
runs.append({"tag": "Run 17", "intake": r17, "governance": r17_gov})
print(f"  → governance={r17_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 18: BNB neutral swing → EXECUTE → FULL CHAIN ---
print("\n=== RUN 18: BNB neutral swing → FULL CHAIN ===")
r18 = intake({
    "symbol": "BNBUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "BNB double bottom at range low with RSI divergence; invalidated if "
             "price closes below range low.",
    "stop_loss": "3%", "max_loss_usdt": 250, "position_size_usdt": 2000,
    "risk_unit_usdt": 200, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.65,
})
r18_gov = govern(r18["id"]) if "id" in r18 else {}
r18_plan = {}; r18_outcome = {}; r18_review = {}
if r18_gov.get("governance_decision") == "execute":
    r18_plan = plan(r18["id"])
    if "execution_receipt_id" in r18_plan:
        r18_outcome = outcome(r18["id"], {
            "execution_receipt_id": r18_plan["execution_receipt_id"],
            "observed_outcome": "BNB bounced +6% from range low, exit at mid-range.",
            "verdict": "validated", "variance_summary": "Clean execution.",
            "plan_followed": True,
        })
        if "outcome_id" in r18_outcome:
            r18_review = submit_review({
                "recommendation_id": None, "review_type": "recommendation_postmortem",
                "expected_outcome": "BNB bounces from range low",
                "actual_outcome": "BNB bounced +6%",
                "deviation": "Clean", "mistake_tags": "range_trading",
                "lessons": [{"lesson_text": "RSI divergence at range lows is a high-confidence reversal signal."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome", "outcome_ref_id": r18_outcome["outcome_id"],
            })
runs.append({"tag": "Run 18", "intake": r18, "governance": r18_gov, "plan": r18_plan, "outcome": r18_outcome, "review": r18_review})
print(f"  intake_id={r18.get('id')} → governance={r18_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 19: DOGE rule_exceptions → ESCALATE ---
print("\n=== RUN 19: DOGE rule_exceptions ===")
r19 = intake({
    "symbol": "DOGEUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "DOGE breaking trendline with volume; invalidated if closes back below trendline.",
    "stop_loss": "4%", "max_loss_usdt": 100, "position_size_usdt": 500,
    "risk_unit_usdt": 50, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.55,
    "rule_exceptions": ["override position limit for event trade"],
})
r19_gov = govern(r19["id"]) if "id" in r19 else {}
runs.append({"tag": "Run 19", "intake": r19, "governance": r19_gov})
print(f"  → governance={r19_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 20: ETH reckless FOMO → REJECT ---
print("\n=== RUN 20: ETH reckless FOMO ===")
r20 = intake({
    "symbol": "ETHUSDT", "timeframe": "5m", "direction": "long",
    "thesis": "ETH just broke ATH, this is the one, going all in",
    "stop_loss": "0.5%", "max_loss_usdt": 10000, "position_size_usdt": 50000,
    "risk_unit_usdt": 2000, "is_revenge_trade": False, "is_chasing": True,
    "emotional_state": "excited", "confidence": 0.95,
})
r20_gov = govern(r20["id"]) if "id" in r20 else {}
runs.append({"tag": "Run 20", "intake": r20, "governance": r20_gov})
print(f"  → governance={r20_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 21: INJ confidence too low → ESCALATE ---
print("\n=== RUN 21: INJ low confidence ===")
r21 = intake({
    "symbol": "INJUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "INJ holding above 200 MA, not sure if this holds though; "
             "invalidated if price closes below 200 MA.",
    "stop_loss": "5%", "max_loss_usdt": 100, "position_size_usdt": 500,
    "risk_unit_usdt": 50, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.2,
})
r21_gov = govern(r21["id"]) if "id" in r21 else {}
runs.append({"tag": "Run 21", "intake": r21, "governance": r21_gov})
print(f"  → governance={r21_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 22: LINK trend continuation → EXECUTE → FULL CHAIN ---
print("\n=== RUN 22: LINK trend continuation → FULL CHAIN ===")
r22 = intake({
    "symbol": "LINKUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "LINK daily higher high sequence with increasing volume, trend intact; "
             "invalidated if price closes below prior day low.",
    "stop_loss": "4%", "max_loss_usdt": 300, "position_size_usdt": 3000,
    "risk_unit_usdt": 300, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.8,
})
r22_gov = govern(r22["id"]) if "id" in r22 else {}
r22_plan = {}; r22_outcome = {}; r22_review = {}
if r22_gov.get("governance_decision") == "execute":
    r22_plan = plan(r22["id"])
    if "execution_receipt_id" in r22_plan:
        r22_outcome = outcome(r22["id"], {
            "execution_receipt_id": r22_plan["execution_receipt_id"],
            "observed_outcome": "LINK continued trend +8%, exited at extended target.",
            "verdict": "validated", "variance_summary": "Better than expected.",
            "plan_followed": True,
        })
        if "outcome_id" in r22_outcome:
            r22_review = submit_review({
                "recommendation_id": None, "review_type": "recommendation_postmortem",
                "expected_outcome": "LINK continues daily uptrend",
                "actual_outcome": "LINK +8% trend continuation",
                "deviation": "Exceeded target", "mistake_tags": "trend_following",
                "lessons": [{"lesson_text": "Daily trend continuation with volume confirmation is high-probability."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome", "outcome_ref_id": r22_outcome["outcome_id"],
            })
runs.append({"tag": "Run 22", "intake": r22, "governance": r22_gov, "plan": r22_plan, "outcome": r22_outcome, "review": r22_review})
print(f"  intake_id={r22.get('id')} → governance={r22_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 23: ATOM stress trade → ESCALATE (emotional + thesis quality) ---
print("\n=== RUN 23: ATOM stressed trader ===")
r23 = intake({
    "symbol": "ATOMUSDT", "timeframe": "1h", "direction": "long",
    "thesis": "ATOM looking decent on the chart, might go up from here; "
             "invalidated if price drops back below the recent low.",
    "stop_loss": "2%", "max_loss_usdt": 150, "position_size_usdt": 1000,
    "risk_unit_usdt": 100, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "stressed", "confidence": 0.5,
})
r23_gov = govern(r23["id"]) if "id" in r23 else {}
runs.append({"tag": "Run 23", "intake": r23, "governance": r23_gov})
print(f"  → governance={r23_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 24: APT thesis too short → ESCALATE ---
print("\n=== RUN 24: APT short thesis ===")
r24 = intake({
    "symbol": "APTUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "APT looking good on volume",
    "stop_loss": "3%", "max_loss_usdt": 100, "position_size_usdt": 500,
    "risk_unit_usdt": 50, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.6,
})
r24_gov = govern(r24["id"]) if "id" in r24 else {}
runs.append({"tag": "Run 24", "intake": r24, "governance": r24_gov})
print(f"  → governance={r24_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 25: AVAX breakdown → EXECUTE → FULL CHAIN ---
print("\n=== RUN 25: AVAX breakdown → FULL CHAIN ===")
r25 = intake({
    "symbol": "AVAXUSDT", "timeframe": "4h", "direction": "short",
    "thesis": "AVAX head and shoulders breakdown with volume spike confirming distribution; "
             "invalidated if price closes back above neckline.",
    "stop_loss": "3%", "max_loss_usdt": 200, "position_size_usdt": 1500,
    "risk_unit_usdt": 150, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "neutral", "confidence": 0.65,
})
r25_gov = govern(r25["id"]) if "id" in r25 else {}
r25_plan = {}; r25_outcome = {}; r25_review = {}
if r25_gov.get("governance_decision") == "execute":
    r25_plan = plan(r25["id"])
    if "execution_receipt_id" in r25_plan:
        r25_outcome = outcome(r25["id"], {
            "execution_receipt_id": r25_plan["execution_receipt_id"],
            "observed_outcome": "AVAX dropped -7%, target exceeded, plan validated.",
            "verdict": "validated", "variance_summary": "Pattern played out cleanly.",
            "plan_followed": True,
        })
        if "outcome_id" in r25_outcome:
            r25_review = submit_review({
                "recommendation_id": None, "review_type": "recommendation_postmortem",
                "expected_outcome": "AVAX breaks down from H&S",
                "actual_outcome": "AVAX dropped -7%",
                "deviation": "Exceeded target", "mistake_tags": "pattern_trading",
                "lessons": [{"lesson_text": "H&S with volume confirmation on 4h is reliable for AVAX."}],
                "new_rule_candidate": "Always wait for volume confirmation on pattern breaks.",
                "outcome_ref_type": "finance_manual_outcome", "outcome_ref_id": r25_outcome["outcome_id"],
            })
runs.append({"tag": "Run 25", "intake": r25, "governance": r25_gov, "plan": r25_plan, "outcome": r25_outcome, "review": r25_review})
print(f"  intake_id={r25.get('id')} → governance={r25_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 26: TIA missing stop_loss → REJECT ---
print("\n=== RUN 26: TIA missing stop_loss ===")
r26 = intake({
    "symbol": "TIAUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "TIA breaking out with volume; invalidated if closes below breakout level.",
    "max_loss_usdt": 200, "position_size_usdt": 1000, "risk_unit_usdt": 100,
    "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.7,
})
r26_gov = govern(r26["id"]) if "id" in r26 else {}
runs.append({"tag": "Run 26", "intake": r26, "governance": r26_gov})
print(f"  → governance={r26_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 27: NEAR greedy → ESCALATE ---
print("\n=== RUN 27: NEAR greedy ===")
r27 = intake({
    "symbol": "NEARUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "NEAR showing strong momentum, want to add to position; invalidated if "
             "price closes below the breakout level.",
    "stop_loss": "4%", "max_loss_usdt": 200, "position_size_usdt": 1500,
    "risk_unit_usdt": 150, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "greedy", "confidence": 0.7,
})
r27_gov = govern(r27["id"]) if "id" in r27 else {}
runs.append({"tag": "Run 27", "intake": r27, "governance": r27_gov})
print(f"  → governance={r27_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 28: UNI conservative → EXECUTE → FULL CHAIN ---
print("\n=== RUN 28: UNI conservative → FULL CHAIN ===")
r28 = intake({
    "symbol": "UNIUSDT", "timeframe": "1d", "direction": "long",
    "thesis": "UNI weekly support with bullish engulfing candle and OBV divergence; "
             "invalidated if price closes below weekly support.",
    "stop_loss": "5%", "max_loss_usdt": 150, "position_size_usdt": 1000,
    "risk_unit_usdt": 100, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.75,
})
r28_gov = govern(r28["id"]) if "id" in r28 else {}
r28_plan = {}; r28_outcome = {}; r28_review = {}
if r28_gov.get("governance_decision") == "execute":
    r28_plan = plan(r28["id"])
    if "execution_receipt_id" in r28_plan:
        r28_outcome = outcome(r28["id"], {
            "execution_receipt_id": r28_plan["execution_receipt_id"],
            "observed_outcome": "UNI rallied +12% from support, exited at mid-range.",
            "verdict": "validated", "variance_summary": "Exceeded target.",
            "plan_followed": True,
        })
        if "outcome_id" in r28_outcome:
            r28_review = submit_review({
                "recommendation_id": None, "review_type": "recommendation_postmortem",
                "expected_outcome": "UNI rallies from weekly support",
                "actual_outcome": "UNI rallied +12%",
                "deviation": "Exceeded target", "mistake_tags": "support_bounce",
                "lessons": [{"lesson_text": "Bullish engulfing at weekly support with OBV divergence is a powerful signal."}],
                "new_rule_candidate": None,
                "outcome_ref_type": "finance_manual_outcome", "outcome_ref_id": r28_outcome["outcome_id"],
            })
runs.append({"tag": "Run 28", "intake": r28, "governance": r28_gov, "plan": r28_plan, "outcome": r28_outcome, "review": r28_review})
print(f"  intake_id={r28.get('id')} → governance={r28_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 29: LDO revenge trade → ESCALATE ---
print("\n=== RUN 29: LDO revenge trade ===")
r29 = intake({
    "symbol": "LDOUSDT", "timeframe": "1h", "direction": "long",
    "thesis": "LDO looks like it might bounce, need to recover losses from earlier; "
             "invalidated if price drops below recent swing low.",
    "stop_loss": "2%", "max_loss_usdt": 150, "position_size_usdt": 800,
    "risk_unit_usdt": 80, "is_revenge_trade": True, "is_chasing": False,
    "emotional_state": "frustrated", "confidence": 0.55,
})
r29_gov = govern(r29["id"]) if "id" in r29 else {}
runs.append({"tag": "Run 29", "intake": r29, "governance": r29_gov})
print(f"  → governance={r29_gov.get('governance_decision')}")

time.sleep(0.2)

# --- Run 30: RNDR borderline reject (just over limit) → REJECT ---
print("\n=== RUN 30: RNDR borderline reject ===")
r30 = intake({
    "symbol": "RNDRUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "RNDR breakout from consolidation pattern with volume confirmation; "
             "invalidated if price closes back into consolidation range.",
    "stop_loss": "4%", "max_loss_usdt": 250, "position_size_usdt": 1100,
    "risk_unit_usdt": 100, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "calm", "confidence": 0.7,
})
r30_gov = govern(r30["id"]) if "id" in r30 else {}
runs.append({"tag": "Run 30", "intake": r30, "governance": r30_gov})
print(f"  → governance={r30_gov.get('governance_decision')} (max_loss/risk_unit=2.5 > 2.0 limit)")

time.sleep(0.2)

# --- Run 31: SUI thesis lacks verifiability + stressed → ESCALATE ---
print("\n=== RUN 31: SUI stressed + no verifiability ===")
r31 = intake({
    "symbol": "SUIUSDT", "timeframe": "4h", "direction": "long",
    "thesis": "SUI is pumping hard today, the chart looks incredible",
    "stop_loss": "3%", "max_loss_usdt": 200, "position_size_usdt": 1000,
    "risk_unit_usdt": 100, "is_revenge_trade": False, "is_chasing": False,
    "emotional_state": "stressed", "confidence": 0.5,
})
r31_gov = govern(r31["id"]) if "id" in r31 else {}
runs.append({"tag": "Run 31", "intake": r31, "governance": r31_gov})
print(f"  → governance={r31_gov.get('governance_decision')}")

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
