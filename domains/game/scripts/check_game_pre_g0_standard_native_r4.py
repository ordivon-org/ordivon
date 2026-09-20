#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "standards/game_pre_g0_standard_native_r4_report.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str):
    return json.loads(read(path))


def item(uid: str, status: str, evidence: str, note: str = "") -> dict:
    return {"uid": uid, "status": status, "evidence": evidence, "note": note}


def main() -> int:
    thesis = load("evidence/acceptance/game-product-thesis-sprint-r1-20260914.json")
    portfolio = load("evidence/acceptance/game-r1-direct-play-portfolio-20260914.json")
    stack = load("evidence/game-development-stack-graduation-r1-20260913.json")
    worksheet = read("docs/GAME_PRE_G0_C0_HUMAN_CANARY_WORKSHEET.md")
    front_half = read("docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md")
    app = read("experiments/pre-g0/web/app.js")
    index = read("experiments/pre-g0/web/index.html")
    styles = read("experiments/pre-g0/web/styles.css")

    human_not_started = portfolio.get("status") == "PORTFOLIO_SELECTED_HUMAN_PLAY_NOT_STARTED_PARALLEL_EXPLORATION_ADMITTED"
    c0_boundary = "C0 does **not**" in worksheet and "C1 Player Value mechanism evidence" in worksheet
    no_sensitive = "Do not record demographics or sensitive personal data" in worksheet
    local_label = "non-sensitive/local only" in worksheet and "localStorage" in app
    semantic_controls = '<input id="participant"' in app and 'aria-label="participant label"' in app and '<button' in app
    alternate_keys = "ArrowLeft" in app and "KeyA" in app and "ArrowRight" in app and "KeyD" in app and "Space" in app and "ArrowUp" in app
    has_canvas = '<canvas id="traversal"' in app
    focus_audit = bool(re.search(r"focus|tabindex|aria-live|skip link", app + index, flags=re.I))
    contrast_explicit = all(token in styles for token in ["--text:", "--bg:", "--muted:", "--accent:"])

    checks = [
        item("GAME-HCD-001", "PASS" if thesis.get("theses") and "product-thesis" in thesis.get("kind", "") else "OPEN", "game-product-thesis-sprint-r1-20260914.json"),
        item("GAME-HCD-002", "PASS" if "Human play / evidence" in front_half and "kill / revise / continue" in front_half else "OPEN", "GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md + C0 worksheet"),
        item("GAME-HCD-003", "OPEN" if human_not_started else "REVIEW_REQUIRED", "direct-play portfolio standing + C0 worksheet", "No real-human C0 canary is recorded in the current portfolio standing."),
        item("GAME-HCD-004", "OPEN" if human_not_started and c0_boundary else "REVIEW_REQUIRED", "C0/C1 boundary", "Automation and apparatus completion do not establish Player Value."),
        item("GAME-HCD-005", "PASS" if "kill / revise / continue" in front_half else "OPEN", "front-half iterative evidence loop"),
        item("GAME-USAB-001", "PASS", "Runtime Job job-01a09dd6-1b54-7392-8b5c-dd4ff8386003: pnpm check 435/435 PASS + pre-G0 Playwright E2E PASS", "This is mechanical apparatus evidence only."),
        item("GAME-USAB-002", "OPEN" if human_not_started else "REVIEW_REQUIRED", "human-play standing", "Human effectiveness/efficiency/satisfaction in context has not yet been observed."),
        item("GAME-A11Y-001", "PARTIAL" if alternate_keys else "OPEN", "PGP-A supports A/D or arrows and Space/Up", "Equivalent keyboard routes exist for some actions, but remapping, alternate devices and full control accessibility are not established."),
        item("GAME-A11Y-002", "PARTIAL" if contrast_explicit else "OPEN", "web carrier defines explicit text/background/muted/accent tokens", "No contrast measurement or human accessibility evaluation is recorded."),
        item("GAME-A11Y-003", "PARTIAL" if semantic_controls else "OPEN", "semantic buttons/input and participant aria-label", "Basic accessible control semantics exist; a complete keyboard/focus/screen-reader audit is not established." if not focus_audit else "Basic semantics plus explicit focus-related behavior observed; full WCAG conformance still not claimed."),
        item("GAME-A11Y-004", "OPEN" if has_canvas else "NOT_APPLICABLE", "PGP-A essential movement is rendered in a visual canvas", "No equivalent non-visual gameplay interaction has been established."),
        item("GAME-PRIV-001", "PASS" if no_sensitive and local_label else "PARTIAL", "C0 worksheet + localStorage apparatus"),
        item("GAME-PRIV-002", "DEFERRED_TRIGGERED_BY_SCOPE_CHANGE", "Current protocol is local and non-sensitive", "Activate broader participant/privacy/research obligations before remote recruitment, account linkage, or sensitive collection."),
        item("GAME-ENG-001", "PASS" if stack.get("engine", {}).get("host", "").startswith("4.7.1") and stack.get("graduation", {}).get("developmentFoundation") == "READY" else "OPEN", "game-development-stack-graduation-r1-20260913.json"),
        item("GAME-ENG-002", "PINNED_NOT_LATEST", "accepted local pin=Godot 4.7.1; upstream stable observed on 2026-09-14=4.7.2", "This is provider-currentness information, not automatic upgrade failure."),
        item("GAME-AGENT-001", "PASS" if thesis.get("agentRequirement") == "NONE_FOR_ALL_R1_THESIS_FALSIFIERS" and "Runtime Agent none" in app else "OPEN", "product-thesis sprint + pre-G0 apparatus"),
        item("GAME-DIST-001", "DEFERRED_NOT_APPLICABLE_CURRENT_PHASE" if not portfolio.get("productSelected") and not portfolio.get("g0Entered") else "REVIEW_REQUIRED", "productSelected=false, g0Entered=false", "Store/rating/platform-release authorities activate after target selection."),
        item("GAME-G0-001", "PASS" if not portfolio.get("productSelected") and not portfolio.get("g0Entered") else "OPEN", "current direct-play portfolio standing"),
    ]

    summary: dict[str, int] = {}
    for check in checks:
        summary[check["status"]] = summary.get(check["status"], 0) + 1

    report = {
        "schemaVersion": 1,
        "kind": "game-pre-g0-standard-native-r4-conformance-observation",
        "date": "2026-09-14",
        "subject": {
            "baselineRevision": "3ac0d1a44a0209a569941d745e7766b1c32a22d1",
            "phase": "PRE_G0_PRODUCT_DISCOVERY_AND_HUMAN_VALUE_FALSIFICATION",
            "productSelected": False,
            "g0Entered": False,
        },
        "authorities": [
            "ISO 9241-210:2019",
            "ISO 9241-11:2018",
            "Xbox Accessibility Guidelines v3.2 advisory guidance",
            "WCAG 2.2 for the web carrier only",
            "Games User Research professional practice",
            "Godot official provider documentation/release currentness",
        ],
        "summary": summary,
        "checks": checks,
        "mechanicalAcceptance": {
            "runtimeJobId": "job-01a09dd6-1b54-7392-8b5c-dd4ff8386003",
            "pnpmCheck": {"tests": 435, "pass": 435, "fail": 0},
            "preG0E2E": "PASS",
            "standing": "APPARATUS_ONLY_C0_UNOBSERVED_C1_UNOBSERVED",
        },
        "providerCurrentness": {
            "acceptedGodotPin": "4.7.1",
            "upstreamStableObserved": "4.7.2",
            "disposition": "PINNED_NOT_LATEST_NO_FORCE_UPDATE",
        },
        "boundary": "This report is a task-local applicability/evidence observation. It is not ISO certification, WCAG conformance, XAG certification, Player Value proof, product selection, G0 admission, ratings approval, store certification, or commercial-release readiness.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
