#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Mapping, Optional
from urllib.parse import parse_qs

import evaluator_reference as er

RENDERER_ID = "ORDIVON_R4_GENERIC_TEXT_UI_V1"
SESSION_SCHEDULE_STRIDE = 13  # coprime to 32 exact eval starts
FIXED_CSS = """body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;line-height:1.45}main{display:grid;gap:18px}.panel{border:1px solid #999;border-radius:8px;padding:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere}.actions{display:flex;flex-wrap:wrap;gap:10px}button{font:inherit;padding:10px 14px}.status{font-weight:700}small{opacity:.75}"""
FIXED_TITLE = "Game"
FIXED_OBSERVATION_HEADING = "State"
FIXED_ACTION_HEADING = "Actions"
FIXED_TERMINAL_COPY = "Round complete"


def eval_start_schedule(model: Mapping) -> list[tuple[int, str]]:
    return [(c, s) for c in range(4) for s in er.initial_states(model, "eval", c)]


def scheduled_start(model: Mapping, participant_ordinal_within_arm: int, episode_index: int) -> tuple[int, str]:
    if not 0 <= participant_ordinal_within_arm < 12:
        raise ValueError("participant ordinal must be 0..11")
    if episode_index < 0:
        raise ValueError("episode index must be non-negative")
    pool = eval_start_schedule(model)
    if len(pool) != 32:
        raise ValueError("renderer requires exactly 32 eval starts")
    idx = (participant_ordinal_within_arm + SESSION_SCHEDULE_STRIDE * episode_index) % len(pool)
    return pool[idx]


def view_model(model: Mapping, state_id: str) -> dict:
    st = model["states"][state_id]
    return {
        "rendererId": RENDERER_ID,
        "status": st["status"],
        "observationJson": er.canonical_json(st["observation"]),
        "legalActions": er.ordered_legal(model, state_id),
    }


def apply_action(model: Mapping, state_id: str, action: str, disabled_coupling: Optional[str] = None) -> str:
    if model["states"][state_id]["status"] != "ONGOING":
        raise ValueError("cannot act from terminal state")
    if action not in er.ordered_legal(model, state_id):
        raise ValueError("illegal action")
    return er.next_state(model, state_id, action, disabled_coupling)


def render_html(model: Mapping, state_id: str, *, terminal_next_round: bool = True) -> str:
    v = view_model(model, state_id)
    status = html.escape(v["status"])
    observation = html.escape(v["observationJson"])
    controls = "".join(
        f'<form method="post" action="/action"><input type="hidden" name="action" value="{html.escape(a, quote=True)}"><button type="submit">{html.escape(a)}</button></form>'
        for a in v["legalActions"]
    )
    if v["status"] != "ONGOING" and terminal_next_round:
        controls = '<form method="post" action="/next-round"><button type="submit">Next round</button></form>'
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{FIXED_TITLE}</title><style>{FIXED_CSS}</style></head><body><main>'
        f'<h1>{FIXED_TITLE}</h1><section class="panel"><div class="status">{status}</div>'
        f'<h2>{FIXED_OBSERVATION_HEADING}</h2><pre>{observation}</pre></section>'
        f'<section class="panel"><h2>{FIXED_ACTION_HEADING}</h2><div class="actions">{controls}</div></section>'
        f'<small>{FIXED_TERMINAL_COPY if v["status"] != "ONGOING" else ""}</small>'
        '</main></body></html>'
    )


def conformance_report(model: Mapping, disabled_coupling: Optional[str] = None) -> dict:
    er.validate_model(model, allow_selftest=(model.get("kind") == "selftest"))
    checked_edges = 0
    checked_views = 0
    for sid in sorted(er.reachable_states(model, disabled_coupling)):
        v = view_model(model, sid)
        st = model["states"][sid]
        assert v["observationJson"] == er.canonical_json(st["observation"])
        assert v["legalActions"] == er.ordered_legal(model, sid)
        assert v["status"] == st["status"]
        rendered = render_html(model, sid)
        # Candidate observations may contain markup-like strings; raw canonical observation must never be injected unescaped.
        assert html.escape(v["observationJson"]) in rendered
        checked_views += 1
        if st["status"] == "ONGOING":
            for action in er.ordered_legal(model, sid):
                assert apply_action(model, sid, action, disabled_coupling) == er.next_state(model, sid, action, disabled_coupling)
                checked_edges += 1
    schedule = eval_start_schedule(model)
    assert len(schedule) == 32
    for ordinal in range(12):
        # 32 episodes with stride 13 visits every exact eval start once for each participant ordinal.
        seen = {scheduled_start(model, ordinal, episode) for episode in range(32)}
        assert len(seen) == 32 and seen == set(schedule)
    return {
        "rendererId": RENDERER_ID,
        "checkedViews": checked_views,
        "checkedEdges": checked_edges,
        "evalStarts": 32,
        "participantOrdinals": 12,
        "candidateSpecificAssetsAllowed": False,
        "externalNetworkAssetsAllowed": False,
        "presentationMapping": "fixed-css+canonical-observation-json+sorted-action-id-buttons+fixed-status",
    }


@dataclass
class Session:
    model: Mapping
    participant_ordinal: int
    disabled_coupling: Optional[str]
    episode_index: int = 0
    state_id: str = ""

    def __post_init__(self) -> None:
        _, self.state_id = scheduled_start(self.model, self.participant_ordinal, self.episode_index)

    def act(self, action: str) -> None:
        self.state_id = apply_action(self.model, self.state_id, action, self.disabled_coupling)

    def next_round(self) -> None:
        if self.model["states"][self.state_id]["status"] == "ONGOING":
            raise ValueError("round is not terminal")
        self.episode_index += 1
        _, self.state_id = scheduled_start(self.model, self.participant_ordinal, self.episode_index)


def serve(model: Mapping, participant_ordinal: int, disabled_coupling: Optional[str], host: str, port: int) -> None:
    er.validate_model(model, allow_selftest=(model.get("kind") == "selftest"))
    session = Session(model, participant_ordinal, disabled_coupling)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int = 200) -> None:
            body = render_html(model, session.state_id).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != "/":
                self.send_error(404); return
            self._send()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            try:
                if self.path == "/action":
                    values = form.get("action", [])
                    if len(values) != 1:
                        raise ValueError("exactly one action required")
                    session.act(values[0])
                elif self.path == "/next-round":
                    session.next_round()
                else:
                    self.send_error(404); return
            except ValueError as exc:
                self.send_error(400, str(exc)); return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, fmt, *args):
            return

    HTTPServer((host, port), Handler).serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--participant-ordinal", type=int, default=0)
    ap.add_argument("--disabled-coupling")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--conformance", action="store_true")
    args = ap.parse_args()
    model = er.load_model(args.model)
    if args.conformance:
        print(json.dumps(conformance_report(model, args.disabled_coupling), sort_keys=True, indent=2))
        return
    serve(model, args.participant_ordinal, args.disabled_coupling, args.host, args.port)


if __name__ == "__main__":
    main()
