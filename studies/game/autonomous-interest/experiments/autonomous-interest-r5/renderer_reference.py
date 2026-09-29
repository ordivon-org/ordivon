#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Mapping, Optional
from urllib.parse import parse_qs

import evaluator_reference as er

RENDERER_ID = "ORDIVON_R5_NEUTRAL_GRID_UI_V1"
SESSION_SCHEDULE_STRIDE = 13
FIXED_TITLE = "Game"
FIXED_OBSERVATION_HEADING = "State"
FIXED_ACTION_HEADING = "Actions"
FIXED_TERMINAL_COPY = "Round complete"
FIXED_CSS = """body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;line-height:1.45}main{display:grid;gap:18px}.panel{border:1px solid #999;border-radius:8px;padding:16px}.grid{display:grid;grid-template-columns:repeat(4,56px);gap:8px}.cell{width:56px;height:56px;border:1px solid #555}.level-0{background:#fff}.level-1{background:#f0f0f0}.level-2{background:#e0e0e0}.level-3{background:#d0d0d0}.level-4{background:#c0c0c0}.level-5{background:#b0b0b0}.level-6{background:#a0a0a0}.level-7{background:#909090}.level-8{background:#808080}.level-9{background:#707070}.level-10{background:#606060}.level-11{background:#505050}.level-12{background:#404040}.level-13{background:#303030}.level-14{background:#202020}.level-15{background:#101010}.actions{display:flex;flex-wrap:wrap;gap:10px}button{font:inherit;padding:10px 14px}.status{font-weight:700}small{opacity:.75}"""


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


def legal_action_ids(model: Mapping, state_id: str) -> list[str]:
    return er.ordered_legal(model, state_id)


def _validate_disabled_coupling(model: Mapping, disabled_coupling: Optional[str]) -> None:
    if disabled_coupling is not None and disabled_coupling not in model["causalCouplings"]:
        raise ValueError("unknown disabled coupling")


def apply_action_ordinal(model: Mapping, state_id: str, ordinal: int, disabled_coupling: Optional[str] = None) -> str:
    _validate_disabled_coupling(model, disabled_coupling)
    if model["states"][state_id]["status"] != "ONGOING":
        raise ValueError("cannot act from terminal state")
    if not 0 <= ordinal < len(model["actions"]):
        raise ValueError("illegal action ordinal")
    action = model["actions"][ordinal]
    if action not in legal_action_ids(model, state_id):
        raise ValueError("action ordinal is not legal in current state")
    return er.next_state(model, state_id, action, disabled_coupling)


def neutral_view(model: Mapping, state_id: str) -> dict:
    st = model["states"][state_id]
    obs = st["observation"]
    if not isinstance(obs, list) or len(obs) != 12 or any(type(v) is not int or not 0 <= v <= 15 for v in obs):
        raise ValueError("renderer requires neutral 12-slot observation")
    return {
        "rendererId": RENDERER_ID,
        "status": st["status"],
        "levels": list(obs),
        "legalActionOrdinals": [model["actions"].index(action) for action in legal_action_ids(model, state_id)],
    }


def render_html(model: Mapping, state_id: str, *, terminal_next_round: bool = True) -> str:
    v = neutral_view(model, state_id)
    cells = "".join(f'<span class="cell level-{level}" aria-hidden="true"></span>' for level in v["levels"])
    controls = "".join(
        f'<form method="post" action="/action"><input type="hidden" name="ordinal" value="{ordinal}"><button type="submit">Action {ordinal+1}</button></form>'
        for ordinal in v["legalActionOrdinals"]
    )
    if v["status"] != "ONGOING" and terminal_next_round:
        controls = '<form method="post" action="/next-round"><button type="submit">Next round</button></form>'
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{FIXED_TITLE}</title><style>{FIXED_CSS}</style></head><body><main>'
        f'<h1>{FIXED_TITLE}</h1><section class="panel"><div class="status">{v["status"]}</div>'
        f'<h2>{FIXED_OBSERVATION_HEADING}</h2><div class="grid">{cells}</div></section>'
        f'<section class="panel"><h2>{FIXED_ACTION_HEADING}</h2><div class="actions">{controls}</div></section>'
        f'<small>{FIXED_TERMINAL_COPY if v["status"] != "ONGOING" else ""}</small>'
        '</main></body></html>'
    )


def conformance_report(model: Mapping, disabled_coupling: Optional[str] = None) -> dict:
    _validate_disabled_coupling(model, disabled_coupling)
    er.validate_model(model, allow_selftest=(model.get("kind") == "selftest"))
    checked_edges = 0
    checked_views = 0
    for sid in sorted(er.reachable_states(model, disabled_coupling)):
        v = neutral_view(model, sid)
        rendered = render_html(model, sid)
        assert v["levels"] == model["states"][sid]["observation"]
        expected_actions = er.ordered_legal(model, sid)
        assert v["legalActionOrdinals"] == [model["actions"].index(action) for action in expected_actions]
        checked_views += 1
        if model["states"][sid]["status"] == "ONGOING":
            for action in expected_actions:
                ordinal = model["actions"].index(action)
                assert apply_action_ordinal(model, sid, ordinal, disabled_coupling) == er.next_state(model, sid, action, disabled_coupling)
                checked_edges += 1
    schedule = eval_start_schedule(model)
    assert len(schedule) == 32
    for ordinal in range(12):
        seen = {scheduled_start(model, ordinal, episode) for episode in range(32)}
        assert len(seen) == 32 and seen == set(schedule)
    return {
        "rendererId": RENDERER_ID,
        "checkedViews": checked_views,
        "checkedEdges": checked_edges,
        "evalStarts": 32,
        "participantOrdinals": 12,
        "candidateControlledVisibleTextAllowed": False,
        "candidateSpecificAssetsAllowed": False,
        "externalNetworkAssetsAllowed": False,
        "presentationMapping": "fixed-neutral-12-cell-grid+protocol-action-ordinals+fixed-status",
    }


@dataclass
class Session:
    model: Mapping
    participant_ordinal: int
    disabled_coupling: Optional[str]
    episode_index: int = 0
    state_id: str = ""

    def __post_init__(self) -> None:
        _validate_disabled_coupling(self.model, self.disabled_coupling)
        _, self.state_id = scheduled_start(self.model, self.participant_ordinal, self.episode_index)

    def act_ordinal(self, ordinal: int) -> None:
        self.state_id = apply_action_ordinal(self.model, self.state_id, ordinal, self.disabled_coupling)

    def next_round(self) -> None:
        if self.model["states"][self.state_id]["status"] == "ONGOING":
            raise ValueError("round is not terminal")
        self.episode_index += 1
        _, self.state_id = scheduled_start(self.model, self.participant_ordinal, self.episode_index)


def serve(model: Mapping, participant_ordinal: int, disabled_coupling: Optional[str], host: str, port: int) -> None:
    _validate_disabled_coupling(model, disabled_coupling)
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
                    values = form.get("ordinal", [])
                    if len(values) != 1:
                        raise ValueError("exactly one action ordinal required")
                    session.act_ordinal(int(values[0]))
                elif self.path == "/next-round":
                    session.next_round()
                else:
                    self.send_error(404); return
            except (ValueError, TypeError) as exc:
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
