#!/usr/bin/env python3
"""Build Browser Decision Corpus R1 from controlled local browser fixtures."""

from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.util
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PROJECTION = ROOT / "research/experiments/browser_ax_projection_v1.py"
GENERALIZATION_DIR = ROOT / "research/fixtures"
JEV_STATIC = Path(
    "/opt/ordivon/external/jev-ultrafast/"
    "452c1ad2dd628008f1d5608f28158d76e49e6cc0/jev_ultrafast/static"
)
JEV_FIXTURE = JEV_STATIC / "fixture.html"

spec = importlib.util.spec_from_file_location("browser_ax_projection_v1", PROJECTION)
assert spec and spec.loader
AX = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AX)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def serve(directory: Path) -> tuple[ThreadingHTTPServer, threading.Thread]:
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def stable_url(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    parsed = urlsplit(raw)
    value = parsed.path
    if parsed.query:
        value += "?" + parsed.query
    if parsed.fragment:
        value += "#" + parsed.fragment
    return value or "/"


def candidate_evidence(candidate: dict[str, Any], context_ref: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "contextRef": context_ref,
        "operation": candidate["operation"],
        "role": candidate.get("role") or "",
        "name": candidate.get("name") or "",
        "context": candidate.get("context") or "",
    }
    description = candidate.get("description")
    if isinstance(description, str) and description:
        evidence["description"] = description
    if candidate.get("optionName") is not None:
        evidence["optionName"] = candidate.get("optionName")
    if candidate.get("value") is not None:
        evidence["value"] = candidate.get("value")
    states = dict(candidate.get("states") or {})
    href = stable_url(states.pop("url", None))
    states.pop("labelledby", None)
    if states:
        evidence["states"] = states
    if href:
        evidence["href"] = href
    candidate_id = "c-" + canonical_digest(evidence).split(":", 1)[1][:16]
    return {"candidateId": candidate_id, **evidence}


def frame_rows(page) -> list[dict[str, Any]]:
    cdp = page.context.new_cdp_session(page)
    dom = cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
    metadata = AX.dom_metadata_from_document(dom)
    frame_tree = cdp.send("Page.getFrameTree")
    rows: list[tuple[str, str, str]] = []

    def walk(node: dict[str, Any], *, root: bool = False) -> None:
        frame = node["frame"]
        fid = frame["id"]
        name = frame.get("name") or ""
        url = stable_url(frame.get("url")) or ""
        rows.append((fid, "main" if root else (name or url), url))
        for child in node.get("childFrames", []) or []:
            walk(child)

    walk(frame_tree["frameTree"], root=True)
    out: list[dict[str, Any]] = []
    for fid, context_ref, _url in rows:
        tree = cdp.send("Accessibility.getFullAXTree", {"frameId": fid})
        projected = AX.project_ax_candidates(
            tree,
            dom_metadata=metadata,
            frame_id=fid,
            require_dom_metadata=True,
        )
        out.extend(candidate_evidence(candidate, context_ref) for candidate in projected)
    seen: set[str] = set()
    for row in out:
        cid = row["candidateId"]
        if cid in seen:
            raise RuntimeError(f"candidate identity collision: {cid}")
        seen.add(cid)
    return sorted(out, key=lambda row: row["candidateId"])


def find_target(candidates: list[dict[str, Any]], spec: dict[str, Any]) -> str:
    matches = []
    for row in candidates:
        if all(row.get(key) == value for key, value in spec.items()):
            matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"target spec must resolve once: {spec!r}; matches={len(matches)}")
    return matches[0]["candidateId"]


CASE_DEFS = [
    # Generalization CLICK
    ("g01-submit", "generalization", "CLICK", "Click the control that submits the application.", {"name": "Submit application"}, "label_direct"),
    ("g02-grant-guide", "generalization", "CLICK", "Open the grant guide.", {"name": "Open grant guide"}, "label_direct"),
    ("g03-email-updates", "generalization", "CLICK", "Toggle email updates.", {"name": "Email updates"}, "state_control"),
    ("g04-remote-participation", "generalization", "CLICK", "Choose remote participation.", {"name": "Remote participation"}, "state_control"),
    ("g05-personal-statement-focus", "generalization", "CLICK", "Focus the personal statement editor without editing it.", {"name": "Personal statement"}, "typed_effect"),
    ("g06-enable-alerts", "generalization", "CLICK", "Enable alerts.", {"name": "Enable alerts"}, "state_control"),
    ("g07-keyword-open", "generalization", "CLICK", "Open or focus the keyword combobox.", {"name": "Keyword combobox"}, "typed_effect"),
    ("g08-fellowship", "generalization", "CLICK", "Apply to the fully funded Houston research fellowship whose deadline is October 31.", {"name": "Apply to fellowship"}, "context_required"),
    ("g09-confirm-eligibility", "generalization", "CLICK", "Confirm eligibility in the open dialog.", {"name": "Confirm eligibility"}, "context_required"),
    ("g10-search-open", "generalization", "CLICK", "Focus the opportunity search field.", {"name": "Opportunity search"}, "typed_effect"),
    ("g11-readonly", "generalization", "CLICK", "Focus the readonly profile field without editing it.", {"name": "Readonly profile"}, "state_required"),
    ("g12-advanced", "generalization", "CLICK", "Expand Advanced options.", {"name": "Advanced options"}, "html_affordance"),
    ("g13-deadlines", "generalization", "CLICK", "Switch to the Deadlines tab.", {"name": "Deadlines"}, "aria_widget"),
    ("g14-save-draft", "generalization", "CLICK", "Save the draft from the actions menu.", {"name": "Save draft"}, "aria_widget"),
    ("g15-private", "generalization", "CLICK", "Choose the Private menu option.", {"name": "Private"}, "aria_widget"),
    ("g16-scholarship-cell", "generalization", "CLICK", "Activate the scholarship grid cell.", {"name": "Scholarship cell"}, "aria_widget"),
    ("g17-nested-button", "generalization", "CLICK", "Activate the nested cell button, not its parent grid cell.", {"name": "Nested cell button"}, "structure_required"),
    ("g18-shadow-apply", "generalization", "CLICK", "Apply to the remote security Shadow Internship.", {"name": "Apply in shadow"}, "shadow_context"),
    ("g19-shadow-search-open", "generalization", "CLICK", "Focus the search control inside the Shadow opportunity.", {"name": "Shadow search"}, "shadow_context"),
    ("g20-frame-apply", "generalization", "CLICK", "Apply for the AI grant inside the embedded frame.", {"name": "Apply in frame", "contextRef": "inner-frame"}, "frame_context"),
    ("g21-frame-query-open", "generalization", "CLICK", "Focus the query field inside the embedded application frame.", {"name": "Frame query", "contextRef": "inner-frame"}, "frame_context"),
    # Generalization FILL
    ("g22-fill-personal", "generalization", "FILL", "Edit the personal statement.", {"name": "Personal statement"}, "typed_effect"),
    ("g23-fill-keyword", "generalization", "FILL", "Enter a new keyword in the keyword combobox.", {"name": "Keyword combobox"}, "typed_effect"),
    ("g24-fill-search", "generalization", "FILL", "Enter a new opportunity search query.", {"name": "Opportunity search"}, "typed_effect"),
    ("g25-fill-name", "generalization", "FILL", "Change the applicant name.", {"name": "Applicant name"}, "typed_effect"),
    ("g26-fill-team", "generalization", "FILL", "Change the team size.", {"name": "Team size"}, "typed_effect"),
    ("g27-fill-shadow", "generalization", "FILL", "Enter a new search inside the Shadow opportunity.", {"name": "Shadow search"}, "shadow_context"),
    ("g28-fill-frame", "generalization", "FILL", "Enter a new query inside the embedded application frame.", {"name": "Frame query", "contextRef": "inner-frame"}, "frame_context"),
    # Generalization SELECT
    ("g29-select-research", "generalization", "SELECT", "Choose the Research track.", {"name": "Track", "optionName": "Research"}, "typed_effect"),
    ("g30-select-industry", "generalization", "SELECT", "Choose the Industry track.", {"name": "Track", "optionName": "Industry"}, "typed_effect"),
    # Travel
    ("t01-free-cancel", "travel", "CLICK", "Enable the free cancellation filter.", {"name": "Free cancellation"}, "state_control"),
    ("t02-reading-room", "travel", "CLICK", "Open the Reading room.", {"name": "Reading room"}, "label_direct"),
    ("t03-find-stays", "travel", "CLICK", "Run the stay search.", {"name": "Find stays"}, "typed_effect"),
    ("t04-casa", "travel", "CLICK", "Open the Lisbon Design stay that has free cancellation and costs €145 per night.", {"name": "View Casa Flora"}, "context_required"),
    ("t05-glasshouse", "travel", "CLICK", "Open the Copenhagen Design stay with free cancellation priced at €210 per night.", {"name": "View The Glasshouse"}, "context_required"),
    ("t06-serra", "travel", "CLICK", "Open the Lisbon Nature stay that is non-refundable and costs €120 per night.", {"name": "View Serra Lodge"}, "context_required"),
    ("t08-design", "travel", "SELECT", "Choose the Design stay category.", {"name": "Stay category", "optionName": "Design"}, "typed_effect"),
    ("t09-nature", "travel", "SELECT", "Choose the Nature stay category.", {"name": "Stay category", "optionName": "Nature"}, "typed_effect"),
    ("t10-coastal", "travel", "SELECT", "Choose the Coastal stay category.", {"name": "Stay category", "optionName": "Coastal"}, "typed_effect"),
    # Research
    ("r01-choice", "research", "CLICK", "Read about finite action sets turning visible browser elements into a fast control loop.", {"name": "A browser is a choice, not a conversation"}, "context_required"),
    ("r02-latency", "research", "CLICK", "Read about measuring network latency, model decisions, and page settling separately.", {"name": "Where the milliseconds go"}, "context_required"),
    ("r03-confidence", "research", "CLICK", "Read what a peaked probability distribution can and cannot establish about correctness.", {"name": "Confidence is not correctness"}, "context_required"),
]


def build(output: Path) -> dict[str, Any]:
    gen_server, _ = serve(GENERALIZATION_DIR)
    jev_server, _ = serve(JEV_STATIC)
    gen_port = gen_server.server_address[1]
    jev_port = jev_server.server_address[1]
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 1500})
            sources: dict[str, list[dict[str, Any]]] = {}
            page.goto(f"http://127.0.0.1:{gen_port}/browser_ax_generalization_r1.html")
            page.frames[1].locator("#frame-button").wait_for()
            sources["generalization"] = frame_rows(page)
            page.goto(f"http://127.0.0.1:{jev_port}/fixture.html?scenario=travel")
            sources["travel"] = frame_rows(page)
            page.goto(f"http://127.0.0.1:{jev_port}/fixture.html?scenario=research")
            sources["research"] = frame_rows(page)
            browser_version = browser.version
            browser.close()
    finally:
        gen_server.shutdown()
        jev_server.shutdown()

    source_meta = {
        "generalization": {
            "fixtureId": "browser_ax_generalization_r1",
            "fixtureDigest": sha256_file(GENERALIZATION_DIR / "browser_ax_generalization_r1.html"),
        },
        "travel": {
            "fixtureId": "jev_fixture_travel",
            "fixtureDigest": sha256_file(JEV_FIXTURE),
            "scenario": "travel",
        },
        "research": {
            "fixtureId": "jev_fixture_research",
            "fixtureDigest": sha256_file(JEV_FIXTURE),
            "scenario": "research",
        },
    }
    projection_digest = sha256_file(PROJECTION)

    cases = []
    for case_id, source_id, operation, goal, target_spec, case_class in CASE_DEFS:
        candidates = [row for row in sources[source_id] if row["operation"] == operation]
        target_id = find_target(candidates, {"operation": operation, **target_spec})
        state = {
            "goal": goal,
            "operation": operation,
            "caseClass": case_class,
            "source": {
                **source_meta[source_id],
                "projectionDigest": projection_digest,
                "chromiumVersion": browser_version,
            },
            "candidates": candidates,
        }
        cases.append({"caseId": case_id, "state": state, "expected": {"target": target_id}})

    corpus = {
        "schemaVersion": 1,
        "kind": "ordivon.system1-decision-corpus",
        "corpusId": "browser-decision-r1-controlled",
        "standing": "CONTROLLED_FIXTURE_ONLY",
        "nonClaims": [
            "representative_open_web_population",
            "production_browser_success",
            "provider_superiority",
            "production_calibration",
        ],
        "questions": {
            "target": {
                "type": "dynamic_choice",
                "candidateSetField": "candidates",
                "instructions": (
                    "Choose the candidate of the already-selected operation type that best "
                    "fulfills the browser goal."
                ),
            }
        },
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return corpus


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "config/browser-decision-corpus-r1.json",
    )
    args = parser.parse_args()
    corpus = build(args.output)
    counts: dict[str, int] = {}
    classes: dict[str, int] = {}
    for case in corpus["cases"]:
        op = case["state"]["operation"]
        counts[op] = counts.get(op, 0) + 1
        cls = case["state"]["caseClass"]
        classes[cls] = classes.get(cls, 0) + 1
    print(
        json.dumps(
            {
                "corpusId": corpus["corpusId"],
                "caseCount": len(corpus["cases"]),
                "operations": counts,
                "caseClasses": classes,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
