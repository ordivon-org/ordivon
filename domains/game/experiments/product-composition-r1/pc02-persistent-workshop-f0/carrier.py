#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

SHAPES = ("circle", "square", "diamond", "bar", "ring")
TRANSFORMS = ("left", "up", "right", "down", "rotate", "grow", "shrink")
BUDGET = 6
CANVAS_WIDTH = 560
CANVAS_HEIGHT = 380


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def horizontal_span(pieces: list[dict]) -> int:
    if not pieces:
        return 0
    left = min(int(p["x"]) for p in pieces)
    right = max(int(p["x"]) + int(p["size"]) for p in pieces)
    return right - left


def intent_satisfied(intent: dict, pieces: list[dict]) -> bool:
    if intent["axis"] != "spread":
        raise ValueError(f"unsupported intent axis: {intent['axis']}")
    span = horizontal_span(pieces)
    if intent["target"] == "wide":
        return span >= 260
    if intent["target"] == "compact":
        return span <= 170
    raise ValueError(f"unsupported spread target: {intent['target']}")


def derive_affordances(pieces: list[dict]) -> list[dict]:
    """Derive later attachment sites from the exact committed artifact geometry."""
    source_digest = canonical_digest(pieces)
    affordances: list[dict] = []
    for piece in pieces:
        x = int(piece["x"]) + int(piece["size"]) + 20
        y = int(piece["y"]) + int(piece["size"]) // 4
        if x + 48 <= CANVAS_WIDTH and y + 48 <= CANVAS_HEIGHT:
            affordances.append(
                {
                    "token": f"attach:{source_digest[7:19]}:{piece['id']}:east",
                    "kind": "attach-existing-primitive",
                    "sourcePieceId": piece["id"],
                    "x": x,
                    "y": y,
                }
            )
    return affordances


def _dimension(status: str, observation: str, preference: str) -> dict:
    return {"status": status, "observation": observation, "preference": preference}


def profile_feedback(profile_id: str, pieces: list[dict]) -> dict:
    """Qualitative context feedback. It has no aggregate score and receives no intent metadata."""
    if profile_id not in {"service_bay", "open_gallery"}:
        raise ValueError(f"unknown profile: {profile_id}")

    span = horizontal_span(pieces)
    has_ring = any(p["shape"] == "ring" for p in pieces)
    distinct_shapes = len({p["shape"] for p in pieces})
    all_axis_aligned = all(int(p["rot"]) % 90 == 0 for p in pieces)
    any_gesture = any(int(p["rot"]) % 90 != 0 for p in pieces)
    suggestions: list[dict] = []

    if profile_id == "service_bay":
        if span <= 170:
            footprint = _dimension("supports", "footprint leaves the service aisle clear", "compact")
        else:
            footprint = _dimension("tension", "footprint crosses the service aisle", "compact")
            suggestions.append(
                {"id": "compress-span", "dimension": "footprint", "action": "move edge pieces inward"}
            )
        if has_ring:
            access = _dimension("supports", "ring primitive exposes a handling point", "ring-present")
        else:
            access = _dimension("tension", "no obvious handling point is present", "ring-present")
            suggestions.append({"id": "add-ring", "dimension": "access", "action": "add a ring primitive"})
        if all_axis_aligned:
            alignment = _dimension("supports", "all pieces remain axis-aligned for fixtures", "axis-aligned")
        else:
            alignment = _dimension("tension", "rotated pieces complicate fixture access", "axis-aligned")
            suggestions.append(
                {"id": "square-rotation", "dimension": "alignment", "action": "return rotated pieces to axis alignment"}
            )
        dimensions = {"footprint": footprint, "access": access, "alignment": alignment}
    else:
        if span >= 260:
            footprint = _dimension("supports", "artifact occupies a broad presentation field", "wide")
        else:
            footprint = _dimension("tension", "artifact reads as compressed in the presentation field", "wide")
            suggestions.append(
                {"id": "expand-span", "dimension": "footprint", "action": "move edge pieces outward"}
            )
        if distinct_shapes >= 3:
            variety = _dimension("supports", "three or more primitive types remain visible", "varied-primitives")
        else:
            variety = _dimension("tension", "primitive vocabulary reads as repetitive", "varied-primitives")
            suggestions.append(
                {"id": "vary-primitive", "dimension": "variety", "action": "introduce another primitive type"}
            )
        if any_gesture:
            gesture = _dimension("supports", "non-axis rotation creates a visible directional gesture", "non-axis-gesture")
        else:
            gesture = _dimension("neutral", "no non-axis gesture is present", "non-axis-gesture")
            suggestions.append(
                {"id": "rotate-one", "dimension": "gesture", "action": "rotate one existing primitive"}
            )
        dimensions = {"footprint": footprint, "variety": variety, "gesture": gesture}

    return {
        "profile": profile_id,
        "authority": "advisory-context-observation",
        "dimensions": dimensions,
        "suggestions": suggestions,
    }


class WorkshopCarrier:
    def __init__(self) -> None:
        self.round = 1
        self.intent: dict | None = None
        self.intent_history: list[dict] = []
        self.pieces: list[dict] = []
        self.revisions: list[dict] = []
        self.context_history: list[dict] = []
        self.preference_decisions: list[dict] = []
        self.affordance_history: list[dict] = []
        self.progress_events: list[dict] = []

    def declare_intent(self, axis: str, target: str) -> None:
        if axis != "spread" or target not in {"wide", "compact"}:
            raise ValueError("PC02-F0 exposes only the bounded spread intent axis")
        self.intent = {"axis": axis, "target": target}
        self.intent_history.append({"round": self.round, **self.intent})

    def add_piece(
        self,
        shape: str,
        x: int,
        y: int,
        *,
        size: int = 64,
        rot: int = 0,
        piece_id: str | None = None,
        source_affordance: str | None = None,
    ) -> str:
        if shape not in SHAPES:
            raise ValueError(f"shape not in reused PGP-I grammar: {shape}")
        if len(self.pieces) >= BUDGET:
            raise ValueError("six-piece PGP-I budget exhausted")
        pid = piece_id or f"p{len(self.pieces) + 1}"
        if any(p["id"] == pid for p in self.pieces):
            raise ValueError(f"duplicate piece id: {pid}")
        if not (0 <= x <= CANVAS_WIDTH - size and 0 <= y <= CANVAS_HEIGHT - size):
            raise ValueError("piece placement outside bounded canvas")
        self.pieces.append(
            {
                "id": pid,
                "shape": shape,
                "x": int(x),
                "y": int(y),
                "size": int(size),
                "rot": int(rot) % 360,
                "sourceAffordance": source_affordance,
            }
        )
        return pid

    def transform(self, piece_id: str, kind: str) -> None:
        if kind not in TRANSFORMS:
            raise ValueError(f"transform not in reused PGP-I transform set: {kind}")
        piece = next((p for p in self.pieces if p["id"] == piece_id), None)
        if piece is None:
            raise ValueError(f"unknown piece: {piece_id}")
        if kind == "left":
            piece["x"] -= 16
        elif kind == "right":
            piece["x"] += 16
        elif kind == "up":
            piece["y"] -= 16
        elif kind == "down":
            piece["y"] += 16
        elif kind == "rotate":
            piece["rot"] = (int(piece["rot"]) + 15) % 360
        elif kind == "grow":
            piece["size"] = min(130, int(piece["size"]) + 10)
        elif kind == "shrink":
            piece["size"] = max(28, int(piece["size"]) - 10)
        piece["x"] = max(0, min(CANVAS_WIDTH - int(piece["size"]), int(piece["x"])))
        piece["y"] = max(0, min(CANVAS_HEIGHT - int(piece["size"]), int(piece["y"])))

    def commit(self, label: str) -> dict:
        if self.intent is None:
            raise RuntimeError("intent axis must be declared before commit")
        if not self.pieces:
            raise RuntimeError("cannot commit an empty artifact")
        snapshot = copy.deepcopy(self.pieces)
        if not intent_satisfied(self.intent, snapshot):
            raise RuntimeError("artifact violates the explicitly declared mechanical intent constraint")
        revision = {
            "id": len(self.revisions) + 1,
            "round": self.round,
            "label": label,
            "parentRevisionId": self.revisions[-1]["id"] if self.revisions else None,
            "pieces": snapshot,
            "artifactDigest": canonical_digest(snapshot),
            "intentAxis": copy.deepcopy(self.intent),
            "intentSatisfied": intent_satisfied(self.intent, snapshot),
            "derivedAffordances": derive_affordances(snapshot),
        }
        self.revisions.append(revision)
        return copy.deepcopy(revision)

    def expose(self, profile_id: str) -> dict:
        if not self.revisions or self.revisions[-1]["round"] != self.round:
            raise RuntimeError("current round requires a committed artifact before context exposure")
        revision = self.revisions[-1]
        entry = {
            "round": self.round,
            "revisionId": revision["id"],
            "artifactDigest": revision["artifactDigest"],
            "feedback": profile_feedback(profile_id, revision["pieces"]),
        }
        self.context_history.append(entry)
        return copy.deepcopy(entry)

    def record_preference_decision(
        self, profile_id: str, suggestion_id: str, decision: str, rationale: str
    ) -> dict:
        if decision not in {"accept", "reject"}:
            raise ValueError("decision must be accept or reject")
        matching = [
            entry
            for entry in self.context_history
            if entry["round"] == self.round and entry["feedback"]["profile"] == profile_id
        ]
        if not matching:
            raise RuntimeError("profile must be exposed in the current round before a preference decision")
        suggestions = {s["id"] for s in matching[-1]["feedback"]["suggestions"]}
        if suggestion_id not in suggestions:
            raise ValueError(f"unknown suggestion for current response: {suggestion_id}")
        record = {
            "round": self.round,
            "profile": profile_id,
            "suggestionId": suggestion_id,
            "decision": decision,
            "rationale": rationale,
        }
        self.preference_decisions.append(record)
        return copy.deepcopy(record)

    def available_affordances(self) -> list[dict]:
        if not self.revisions:
            return []
        return copy.deepcopy(self.revisions[-1]["derivedAffordances"])

    def attach_from_commit(self, anchor_token: str, shape: str, *, size: int = 48, rot: int = 0) -> str:
        if not self.revisions:
            raise RuntimeError("artifact-derived attachment requires a prior commit")
        anchor = next(
            (a for a in self.revisions[-1]["derivedAffordances"] if a["token"] == anchor_token),
            None,
        )
        if anchor is None:
            raise ValueError("attachment token is not derived from the latest committed artifact")
        piece_id = self.add_piece(
            shape,
            int(anchor["x"]),
            int(anchor["y"]),
            size=size,
            rot=rot,
            source_affordance=anchor_token,
        )
        self.affordance_history.append(
            {
                "round": self.round,
                "sourceRevisionId": self.revisions[-1]["id"],
                "sourceArtifactDigest": self.revisions[-1]["artifactDigest"],
                "affordanceToken": anchor_token,
                "newPieceId": piece_id,
            }
        )
        return piece_id

    def advance_round(self) -> int:
        if not self.revisions or self.revisions[-1]["round"] != self.round:
            raise RuntimeError("commit current round before progression")
        if not any(entry["round"] == self.round for entry in self.context_history):
            raise RuntimeError("expose current commit to one context before progression")
        # Deliberately does not inspect accept/reject or any context status.
        self.progress_events.append(
            {
                "fromRound": self.round,
                "revisionId": self.revisions[-1]["id"],
                "gate": "commit+context-observed; audience preference is non-authoritative",
            }
        )
        self.round += 1
        return self.round

    def snapshot(self) -> dict:
        return {
            "round": self.round,
            "intent": copy.deepcopy(self.intent),
            "intentHistory": copy.deepcopy(self.intent_history),
            "workingPieces": copy.deepcopy(self.pieces),
            "revisions": copy.deepcopy(self.revisions),
            "contextHistory": copy.deepcopy(self.context_history),
            "preferenceDecisions": copy.deepcopy(self.preference_decisions),
            "affordanceHistory": copy.deepcopy(self.affordance_history),
            "progressEvents": copy.deepcopy(self.progress_events),
        }

    @classmethod
    def from_snapshot(cls, state: dict) -> "WorkshopCarrier":
        carrier = cls()
        carrier.round = int(state["round"])
        carrier.intent = copy.deepcopy(state["intent"])
        carrier.intent_history = copy.deepcopy(state["intentHistory"])
        carrier.pieces = copy.deepcopy(state["workingPieces"])
        carrier.revisions = copy.deepcopy(state["revisions"])
        carrier.context_history = copy.deepcopy(state["contextHistory"])
        carrier.preference_decisions = copy.deepcopy(state["preferenceDecisions"])
        carrier.affordance_history = copy.deepcopy(state.get("affordanceHistory", []))
        carrier.progress_events = copy.deepcopy(state["progressEvents"])
        return carrier

    def save_state(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2, sort_keys=True) + "\n")

    @classmethod
    def load_state(cls, path: Path) -> "WorkshopCarrier":
        return cls.from_snapshot(json.loads(path.read_text()))
