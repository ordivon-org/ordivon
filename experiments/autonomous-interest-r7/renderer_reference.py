#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Mapping, Optional
from urllib.parse import parse_qs

import evaluator_reference as er

RENDERER_ID = "ORDIVON_R7_BLINDED_TOKEN_UI_V1"
PRESENTATION_DOMAIN = "ordivon-r7-blinded-token-map-v1"
SESSION_SCHEDULE_STRIDE = 13
FIXED_TITLE = "Game"
FIXED_OBSERVATION_HEADING = "State"
FIXED_ACTION_HEADING = "Actions"
FIXED_TERMINAL_COPY = "Round complete"
FIXED_CSS = """body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;line-height:1.45}main{display:grid;gap:18px}.panel{border:1px solid #999;border-radius:8px;padding:16px}.tokenbox{height:150px;display:grid;place-items:center}.token{display:block;width:86px;height:86px;background:hsl(var(--h) 58% 52%);border:10px solid #222;box-sizing:border-box}.shape-0{border-radius:50%}.shape-1{border-radius:16%}.shape-2{transform:rotate(45deg);width:66px;height:66px}.shape-3{border-radius:50% 12% 50% 12%}.shape-4{clip-path:polygon(50% 0,100% 100%,0 100%)}.shape-5{clip-path:polygon(50% 0,100% 38%,81% 100%,19% 100%,0 38%)}.shape-6{clip-path:polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%)}.shape-7{clip-path:polygon(50% 0,63% 35%,100% 35%,70% 57%,82% 100%,50% 73%,18% 100%,30% 57%,0 35%,37% 35%)}.border-0{border-style:solid}.border-1{border-style:double}.border-2{border-style:dashed}.border-3{border-style:dotted}.actions{display:flex;flex-wrap:wrap;gap:10px}button{font:inherit;padding:10px 14px}.status{font-weight:700}small{opacity:.75}"""


def eval_start_schedule(model: Mapping) -> list[tuple[int, str]]:
    # Human arm schedule is fixed from normal-world semantics for winner/ablation symmetry.
    return [(c, s) for c in range(4) for s in er.initial_states(model, "eval", c, None)]


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


def _token_permutation(presentation_seed: str, participant_ordinal: int) -> list[int]:
    if not isinstance(presentation_seed,str) or not presentation_seed.startswith("sha256:"):
        raise ValueError("invalid presentation seed")
    if not 0 <= participant_ordinal < 24:
        raise ValueError("presentation participant ordinal must be 0..23")
    ids=list(range(256))
    ids.sort(key=lambda i: hashlib.sha256(f"{PRESENTATION_DOMAIN}|{presentation_seed}|{participant_ordinal}|{i}".encode()).digest())
    return ids


def blinded_token_id(model: Mapping, state_id: str, presentation_seed: str, participant_ordinal: int) -> int:
    canonical_class=er.canonical_observation_class(model,state_id)
    return _token_permutation(presentation_seed,participant_ordinal)[canonical_class]


def token_style(token_id: int) -> dict:
    if not 0 <= token_id < 256: raise ValueError("token id out of range")
    return {"hue":(token_id*137+29)%360,"shape":token_id%8,"border":(token_id//8)%4}


def neutral_view(model: Mapping, state_id: str, *, presentation_seed: str, participant_ordinal: int) -> dict:
    st = model["states"][state_id]
    token=blinded_token_id(model,state_id,presentation_seed,participant_ordinal)
    return {
        "rendererId": RENDERER_ID,
        "status": st["status"],
        "observationToken": token,
        "tokenStyle": token_style(token),
        "legalActionOrdinals": [model["actions"].index(action) for action in legal_action_ids(model, state_id)],
    }


def render_html(model: Mapping, state_id: str, *, presentation_seed: str, participant_ordinal: int,
                terminal_next_round: bool = True) -> str:
    v = neutral_view(model, state_id, presentation_seed=presentation_seed, participant_ordinal=participant_ordinal)
    style=v["tokenStyle"]
    token = f'<span class="token shape-{style["shape"]} border-{style["border"]}" style="--h:{style["hue"]}deg" aria-label="State token"></span>'
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
        f'<h2>{FIXED_OBSERVATION_HEADING}</h2><div class="tokenbox">{token}</div></section>'
        f'<section class="panel"><h2>{FIXED_ACTION_HEADING}</h2><div class="actions">{controls}</div></section>'
        f'<small>{FIXED_TERMINAL_COPY if v["status"] != "ONGOING" else ""}</small>'
        '</main></body></html>'
    )


def conformance_report(model: Mapping, disabled_coupling: Optional[str] = None, *, presentation_seed: str,
                       participant_ordinals=range(24)) -> dict:
    _validate_disabled_coupling(model, disabled_coupling)
    er.validate_model(model, allow_selftest=(model.get("kind") == "selftest"))
    checked_edges = 0; checked_views = 0; observed_tokens=set()
    for participant in participant_ordinals:
        for sid in sorted(er.reachable_states(model, disabled_coupling)):
            v = neutral_view(model, sid, presentation_seed=presentation_seed, participant_ordinal=participant)
            rendered = render_html(model, sid, presentation_seed=presentation_seed, participant_ordinal=participant)
            assert str(model["states"][sid]["observationClass"]) not in rendered or model["states"][sid]["observationClass"] in range(10)
            assert "grid-template-columns" not in rendered
            observed_tokens.add((participant,v["observationToken"]))
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
        "participantOrdinals": len(list(participant_ordinals)),
        "candidateControlledVisibleTextAllowed": False,
        "candidateControlledVisiblePixelsAllowed": False,
        "candidateSpecificAssetsAllowed": False,
        "externalNetworkAssetsAllowed": False,
        "presentationMapping": "post-fix participant-specific blinded single-token map over canonical observation-equivalence classes",
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


def serve(model: Mapping, participant_ordinal: int, disabled_coupling: Optional[str], presentation_seed: str, host: str, port: int) -> None:
    _validate_disabled_coupling(model, disabled_coupling)
    er.validate_model(model, allow_selftest=(model.get("kind") == "selftest"))
    session = Session(model, participant_ordinal % 12, disabled_coupling)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int = 200) -> None:
            body = render_html(model, session.state_id, presentation_seed=presentation_seed, participant_ordinal=participant_ordinal).encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path != "/": self.send_error(404); return
            self._send()
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0")); form = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            try:
                if self.path == "/action":
                    values = form.get("ordinal", [])
                    if len(values) != 1: raise ValueError("exactly one action ordinal required")
                    session.act_ordinal(int(values[0]))
                elif self.path == "/next-round": session.next_round()
                else: self.send_error(404); return
            except (ValueError, TypeError) as exc: self.send_error(400, str(exc)); return
            self.send_response(303); self.send_header("Location", "/"); self.end_headers()
        def log_message(self, fmt, *args): return

    HTTPServer((host, port), Handler).serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--participant-ordinal", type=int, default=0); ap.add_argument("--disabled-coupling"); ap.add_argument("--presentation-seed", required=True); ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=8765); ap.add_argument("--conformance", action="store_true")
    args = ap.parse_args(); model = er.load_model(args.model)
    if args.conformance:
        print(json.dumps(conformance_report(model, args.disabled_coupling, presentation_seed=args.presentation_seed), sort_keys=True, indent=2)); return
    serve(model, args.participant_ordinal, args.disabled_coupling, args.presentation_seed, args.host, args.port)


if __name__ == "__main__": main()
