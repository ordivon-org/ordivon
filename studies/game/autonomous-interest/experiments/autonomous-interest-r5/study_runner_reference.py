#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs

import evaluator_reference as er
import renderer_reference as rr

STUDY_RUNNER_ID = "ORDIVON_R5_HOLDOUT_RUNNER_V1"
ASSIGNMENT_SEED = "ordivon-r5-holdout-arm-assignment-v1"
TOTAL_PARTICIPANTS = 24
PER_ARM = 12
MANDATORY_MS = 8 * 60 * 1000
OPTIONAL_MAX_MS = 12 * 60 * 1000
CONTINUATION_TARGET_MS = 3 * 60 * 1000
HEARTBEAT_INTERVAL_MS = 5_000
HEARTBEAT_MAX_GAP_MS = 6_500
FIXED_CHOICE_COPY = "The required portion is complete. You receive full compensation whether you stop now or continue. Would you like to continue playing?"
FIXED_STOP_LABEL = "Stop now"
FIXED_CONTINUE_LABEL = "Continue playing"
FIXED_DONE_COPY = "Session complete"


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def winner_ordinals() -> frozenset[int]:
    ranked = sorted(range(TOTAL_PARTICIPANTS), key=lambda i: _digest_text(f"{ASSIGNMENT_SEED}|{i}"))
    return frozenset(ranked[:PER_ARM])


WINNER_ORDINALS = winner_ordinals()
assert len(WINNER_ORDINALS) == PER_ARM


def arm_for(enrollment_ordinal: int) -> str:
    if not 0 <= enrollment_ordinal < TOTAL_PARTICIPANTS:
        raise ValueError("enrollment ordinal must be 0..23")
    return "winner" if enrollment_ordinal in WINNER_ORDINALS else "ablation"


def within_arm_ordinal(enrollment_ordinal: int) -> int:
    arm = arm_for(enrollment_ordinal)
    peers = [i for i in range(TOTAL_PARTICIPANTS) if arm_for(i) == arm]
    return peers.index(enrollment_ordinal)


def disabled_coupling_for(enrollment_ordinal: int, matched_coupling: str) -> Optional[str]:
    return None if arm_for(enrollment_ordinal) == "winner" else matched_coupling


@dataclass
class StudyMachine:
    enrollment_ordinal: int
    events: list[dict] = field(default_factory=list)
    choice: Optional[str] = None
    continue_elapsed_ms: Optional[int] = None
    stop_elapsed_ms: Optional[int] = None
    active_mandatory_ms: int = 0
    active_optional_ms: int = 0
    _last_elapsed_ms: int = -1
    _last_valid_heartbeat_ms: Optional[int] = None

    def __post_init__(self) -> None:
        arm_for(self.enrollment_ordinal)

    @property
    def arm(self) -> str:
        return arm_for(self.enrollment_ordinal)

    @property
    def participant_ordinal_within_arm(self) -> int:
        return within_arm_ordinal(self.enrollment_ordinal)

    def optional_deadline_ms(self) -> Optional[int]:
        return None if self.continue_elapsed_ms is None else self.continue_elapsed_ms + OPTIONAL_MAX_MS

    def phase(self, elapsed_ms: int) -> str:
        if elapsed_ms < 0:
            raise ValueError("elapsed time must be non-negative")
        if self.stop_elapsed_ms is not None:
            return "TERMINAL"
        if self.active_mandatory_ms < MANDATORY_MS:
            return "MANDATORY"
        if self.choice is None:
            return "CHOICE"
        if self.choice == "stop":
            return "TERMINAL"
        deadline = self.optional_deadline_ms()
        if deadline is not None and elapsed_ms >= deadline:
            return "TERMINAL"
        return "OPTIONAL"

    def _append(self, elapsed_ms: int, kind: str, **fields) -> dict:
        if elapsed_ms < self._last_elapsed_ms:
            raise ValueError("server elapsed time must be monotonic")
        self._last_elapsed_ms = elapsed_ms
        event = {"seq": len(self.events), "elapsedMs": elapsed_ms, "kind": kind, **fields}
        self.events.append(event)
        return event

    def record_action(self, elapsed_ms: int) -> dict:
        if self.phase(elapsed_ms) not in {"MANDATORY", "OPTIONAL"}:
            raise ValueError("gameplay action outside playable phase")
        return self._append(elapsed_ms, "action")

    def record_continue(self, elapsed_ms: int) -> dict:
        if self.phase(elapsed_ms) != "CHOICE":
            raise ValueError("continue only allowed at choice boundary")
        self.choice = "continue"
        self.continue_elapsed_ms = elapsed_ms
        self._last_valid_heartbeat_ms = None
        return self._append(elapsed_ms, "continue")

    def record_stop(self, elapsed_ms: int) -> dict:
        if self.phase(elapsed_ms) not in {"CHOICE", "OPTIONAL"}:
            raise ValueError("stop only allowed after mandatory phase")
        self.choice = "stop"
        self.stop_elapsed_ms = elapsed_ms
        return self._append(elapsed_ms, "stop")

    def record_heartbeat(self, elapsed_ms: int, *, visible: bool, focused: bool) -> dict:
        phase = self.phase(elapsed_ms)
        event = self._append(elapsed_ms, "heartbeat", visible=bool(visible), focused=bool(focused), phase=phase)
        if phase not in {"MANDATORY", "OPTIONAL"} or not visible or not focused:
            self._last_valid_heartbeat_ms = None
            return event
        deadline = self.optional_deadline_ms() if phase == "OPTIONAL" else None
        effective = elapsed_ms if deadline is None else min(elapsed_ms, deadline)
        if self._last_valid_heartbeat_ms is not None:
            gap = effective - self._last_valid_heartbeat_ms
            if 0 <= gap <= HEARTBEAT_MAX_GAP_MS:
                if phase == "MANDATORY":
                    self.active_mandatory_ms = min(MANDATORY_MS, self.active_mandatory_ms + gap)
                else:
                    self.active_optional_ms += gap
        self._last_valid_heartbeat_ms = effective
        return event

    @property
    def voluntary_continuation_3m(self) -> bool:
        return self.choice == "continue" and self.active_optional_ms >= CONTINUATION_TARGET_MS

    def summary(self) -> dict:
        return {
            "studyRunnerId": STUDY_RUNNER_ID,
            "enrollmentOrdinal": self.enrollment_ordinal,
            "arm": self.arm,
            "participantOrdinalWithinArm": self.participant_ordinal_within_arm,
            "choice": self.choice,
            "activeMandatoryMs": self.active_mandatory_ms,
            "activeOptionalMs": self.active_optional_ms,
            "voluntaryContinuation3m": self.voluntary_continuation_3m,
        }


def heartbeat_script() -> str:
    # Candidate bytes never enter this protocol-owned script.
    return f'''<script>
async function beat(){{
  if(document.visibilityState==='visible' && document.hasFocus()){{
    try{{await fetch('/heartbeat',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'visible=1&focused=1',cache:'no-store'}});}}catch(e){{}}
  }}
}}
setInterval(beat,{HEARTBEAT_INTERVAL_MS});
beat();
</script>'''


def choice_html() -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Game</title></head><body><main><p>'+FIXED_CHOICE_COPY+'</p>'
            '<form method="post" action="/choice"><button name="choice" value="stop">'+FIXED_STOP_LABEL+'</button>'
            '<button name="choice" value="continue">'+FIXED_CONTINUE_LABEL+'</button></form></main></body></html>')


def done_html() -> str:
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Game</title></head><body><main><p>'+FIXED_DONE_COPY+'</p></main></body></html>'


def append_event_log(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)


def serve(candidate_models: list[dict], manifest: dict, enrollment_ordinal: int, log_path: Path, host: str, port: int) -> None:
    import build_manifest_reference as bm
    checked=bm.validate_manifest(manifest,candidate_models)
    model=bm.winner_model_for_manifest(checked,candidate_models)
    selected=checked["selectedCouplingId"]
    arm=arm_for(enrollment_ordinal)
    disabled=checked["armBindings"][arm]["disabledCoupling"]
    if disabled != disabled_coupling_for(enrollment_ordinal,selected):
        raise ValueError("manifest arm binding mismatch")
    rr.conformance_report(model,disabled)
    game=rr.Session(model,within_arm_ordinal(enrollment_ordinal),disabled)
    study=StudyMachine(enrollment_ordinal)
    started_ns=time.monotonic_ns()

    def elapsed_ms() -> int:
        return (time.monotonic_ns()-started_ns)//1_000_000

    append_event_log(log_path,{"seq":-1,"elapsedMs":0,"kind":"session-start",**study.summary(),"manifestDigest":checked["manifestDigest"],"winnerModelDigest":checked["winnerModelDigest"],"disabledCoupling":disabled})

    class Handler(BaseHTTPRequestHandler):
        def _body(self,body:str,code:int=200)->None:
            raw=body.encode("utf-8"); self.send_response(code); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(raw))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(raw)
        def _redirect(self)->None:
            self.send_response(303); self.send_header("Location","/"); self.end_headers()
        def do_GET(self):
            if self.path!="/": self.send_error(404); return
            now=elapsed_ms(); phase=study.phase(now)
            if phase=="CHOICE": self._body(choice_html()); return
            if phase=="TERMINAL": self._body(done_html()); return
            body=rr.render_html(model,game.state_id).replace('</body>',heartbeat_script()+'</body>'); self._body(body)
        def do_POST(self):
            now=elapsed_ms(); length=int(self.headers.get("Content-Length","0")); form=parse_qs(self.rfile.read(length).decode("utf-8"),keep_blank_values=True)
            try:
                if self.path=="/heartbeat":
                    ev=study.record_heartbeat(now,visible=form.get("visible")==["1"],focused=form.get("focused")==["1"]); append_event_log(log_path,ev); self.send_response(204); self.end_headers(); return
                if self.path=="/choice":
                    choice=form.get("choice",[])
                    if choice==["continue"]: ev=study.record_continue(now)
                    elif choice==["stop"]: ev=study.record_stop(now)
                    else: raise ValueError("invalid choice")
                    append_event_log(log_path,ev); self._redirect(); return
                if self.path=="/action":
                    values=form.get("ordinal",[])
                    if len(values)!=1: raise ValueError("exactly one action ordinal required")
                    ev=study.record_action(now); game.act_ordinal(int(values[0])); append_event_log(log_path,ev); self._redirect(); return
                if self.path=="/next-round":
                    ev=study.record_action(now); game.next_round(); append_event_log(log_path,ev); self._redirect(); return
                self.send_error(404)
            except (ValueError,TypeError) as exc: self.send_error(400,str(exc))
        def log_message(self,fmt,*args): return

    HTTPServer((host,port),Handler).serve_forever()

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("models",nargs="+",help="exact three candidate model JSON files")
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--enrollment-ordinal",type=int,required=True)
    ap.add_argument("--log",required=True)
    ap.add_argument("--host",default="127.0.0.1")
    ap.add_argument("--port",type=int,default=8765)
    args=ap.parse_args()
    if len(args.models)!=3: raise SystemExit("exactly three candidate models required")
    models=[er.load_model(x) for x in args.models]
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    serve(models,manifest,args.enrollment_ordinal,Path(args.log),args.host,args.port)


if __name__=="__main__": main()
