#!/usr/bin/env python3
"""Deterministic non-Human browser gate for CS2-03.

This exercises the complete 4x4 apparatus, reflections, and JSON export. It is
mechanical/browser evidence only and must never be promoted to Human evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765/web/")
    ap.add_argument("--chromium", help="Explicit Chromium executable when Playwright browser cache discovery is not authoritative")
    ap.add_argument("--out", type=Path, default=Path("/tmp/cs2-03-prehuman-playwright"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        launch = {"headless": True}
        if args.chromium:
            launch.update({"executable_path": args.chromium, "args": ["--no-sandbox"]})
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        page.goto(args.url, wait_until="networkidle")
        assert "four very short build runs" in page.locator("#app").inner_text()
        page.get_by_role("button", name="Begin").click()

        visibility_sequence: list[str] = []
        choice_labels: list[str] = []
        for run in range(4):
            for rnd in range(4):
                body = page.locator("#app").inner_text()
                assert f"Run {run + 1} of 4" in body
                assert f"Round {rnd + 1} of 4" in body
                visible = "Current challenge visible" in body
                concealed = "Current challenge concealed" in body
                assert visible ^ concealed
                visibility_sequence.append("UPSTREAM" if visible else "DOWNSTREAM")

                cards = page.locator("button.card")
                assert cards.count() >= 2
                labels = [cards.nth(i).locator("strong").inner_text() for i in range(cards.count())]
                idx = (run + rnd) % cards.count()
                choice = labels[idx]
                choice_labels.append(choice)
                cards.nth(idx).click()
                result = page.locator("#app").inner_text()
                assert choice in result and "round score" in result
                page.get_by_role("button", name="Complete run" if rnd == 3 else "Next round").click()

            assert f"Run {run + 1} reflection" in page.locator("#app").inner_text()
            sliders = page.locator("input[type=range]")
            assert sliders.count() == 4
            for i, value in enumerate([2 + run, 3 + run, 4, 5]):
                sliders.nth(i).fill(str(min(value, 7)))
            page.locator("textarea").fill(
                f"AUTOMATED NONHUMAN regression run {run + 1}; no player-value interpretation."
            )
            page.get_by_role("button", name="Save reflection and continue").click()

        assert "Study complete" in page.locator("#app").inner_text()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Export session JSON").click()
        download = download_info.value
        target = args.out / download.suggested_filename
        download.save_as(str(target))
        session = json.loads(target.read_text())

        assert len(session["runs"]) == 4
        assert sum(len(r["rounds"]) for r in session["runs"]) == 16
        assert sorted(r["condition"] for r in session["runs"]) == [
            "DOWNSTREAM",
            "DOWNSTREAM",
            "UPSTREAM",
            "UPSTREAM",
        ]
        assert visibility_sequence == sum(([r["condition"]] * 4 for r in session["runs"]), [])

        receipt = {
            "standing": "PASS_DETERMINISTIC_BROWSER_REGRESSION",
            "humanEvidence": "UNASSESSED_NONHUMAN_ONLY",
            "url": args.url,
            "browserExecutable": args.chromium,
            "session": str(target),
            "schedule": session["schedule"],
            "runs": 4,
            "choices": 16,
            "visibilitySequence": visibility_sequence,
            "choiceLabels": choice_labels,
            "downloadBytes": target.stat().st_size,
            "boundary": "Mechanical/browser regression only; no Human Player Value or condition-effect claim is authorized.",
        }
        print(json.dumps(receipt, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
