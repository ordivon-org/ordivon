#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "experiments/veilwild-r1/contracts/F18_PLAYER_INTERACTION_RUNTIME_CONTRACT_R1.json"
PLAYER = ROOT / "experiments/veilwild-r1/godot/player/player_controller.gd"
UI = ROOT / "experiments/veilwild-r1/godot/player/player_ui.gd"
PLAYER_SCENE = ROOT / "experiments/veilwild-r1/godot/player/player_runtime.tscn"

EXPECTED_INPUTS = {
    "A01/F01": ("66040f75d505e40e0069412b419e380daa5c73fc", "0ded284f7f5b03f782d30fd3d5fce38216f727560efa7b9e1270ec1e13c1fbfb"),
    "A02/F02": ("b0ad6d244f4321ec008744434623723f0095bdfa", "6e947124669cb0e6f131a9fcb51397080bad651394bc612f30fe1ecff42337ee"),
    "A17/F17": ("2cdc6ca3da332dc7c49ea0d26d0e1fcf88478eab", "4fc8ff7b20ee9e48e1fbab1c472cd6ad21930902087ab1125ed19589af5553d2"),
    "A21/F22+F24": ("50db2feb750b8dd3e752cd42b9bf452783dabc32", "fc141dbd88a4b00732bd7ded03f0507fb84def1404587f0c1299446282616556"),
    "A22/F23": ("47b596dffdf7f3d29443854acd802e0cf7ec2894", "d27a9996b065ec05e1996e0bd31c94787d8b5505fa7cde0ab1de61c12556e80b"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"VEILWILD_F18_CONTRACT_INVALID: {message}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads(CONTRACT.read_text())
    require(data["producer"]["agentId"] == "A25", "producer must be A25")
    require(data["producer"]["frontId"] == "F18", "front must be F18")
    require(data["sourceBaseline"] == "8ebc23144ed5b49d685cc32ac11428bbddf64d2f", "baseline drift")

    consumed = {entry["producer"]: entry for entry in data["consumedContracts"]}
    for producer, (commit, digest) in EXPECTED_INPUTS.items():
        require(producer in consumed, f"missing current input {producer}")
        require(consumed[producer]["commit"] == commit, f"stale commit for {producer}")
        require(consumed[producer]["sha256"] == digest, f"stale digest for {producer}")

    observe = data["observeBoundary"]
    require(observe["successOwnedHere"] is False, "A25 must not own observation success")
    require(observe["observationCommittedOwnedHere"] is False, "A25 must not own observation commitment")
    require(observe["eventStart"]["eventType"] == "observe_action_started", "F22 observe start type drift")
    require(observe["eventCancel"]["eventType"] == "observe_action_cancelled", "F22 observe cancel type drift")

    inputs = data["inputContract"]
    require(inputs["observeDefaultActivation"] == "SINGLE_PRESS", "observe must have non-hold default")
    require(set(inputs["observeActivationChoices"]) >= {"SINGLE_PRESS", "TOGGLE"}, "observe alternative activation missing")
    require(all(item["remappable"] for item in inputs["semanticActions"]), "required semantic action not remappable")
    require(all(not item["requiresChord"] for item in inputs["semanticActions"]), "required semantic action is chord-only")
    require(inputs["promptReflectsRemap"] is True, "remapped prompt propagation missing")

    camera = data["cameraCondition"]
    require(camera["lookSensitivityMultiplierRange"][0] <= 0.5, "look sensitivity cannot reach 50%")
    require(camera["lookSensitivityMultiplierRange"][1] >= 1.5, "look sensitivity cannot reach +50%")
    require(camera["independentInvertX"] and camera["independentInvertY"], "independent look inversion missing")
    require(camera["fovRangeDegrees"][0] < camera["defaultFovDegrees"] < camera["fovRangeDegrees"][1], "FOV not adjustable around default")
    require(camera["nonEssentialCameraBob"] is False and camera["nonEssentialCameraShake"] is False, "nonessential camera motion enabled")

    ui = data["uiFeedbackBoundary"]
    require(ui["exactTargetWorldPositionInput"] is False, "locator channel forbidden")
    require(ui["rawHiddenCreatureStateInput"] is False, "hidden-state channel forbidden")
    require(ui["baseTextPixels"] >= 18, "base text below 18 px")
    require(ui["textScalePercentRange"][1] >= 200, "200% text scale missing")
    require(ui["opaqueContrastBackingAvailable"] is True, "critical UI opaque backing missing")
    require(ui["colorOnlyCriticalMeaning"] is False, "critical UI relies on color only")
    require(ui["remappedPromptPropagation"] is True, "UI prompt does not track remap")

    body = data["playerBody"]
    require(body["physicsCollisionLayerMaskValue"] == 2, "player collision layer must be 2")
    require(body["physicsCollisionMaskValue"] == 1, "player collision mask must be 1")
    require(body["motionMode"] == "GROUNDED", "player motion mode must be GROUNDED")
    require(abs(body["floorMaxAngleDegrees"] - 45.0) < 1e-6, "floor max angle drift")
    require(abs(body["floorSnapLengthMeters"] - 0.1) < 1e-6, "floor snap drift")

    player_source = PLAYER.read_text()
    ui_source = UI.read_text()
    scene_source = PLAYER_SCENE.read_text()
    require("signal observe_requested" in player_source, "explicit observe signal missing")
    require("observation_succeeded" not in player_source, "success ownership leaked into controller")
    require('OBSERVE_STARTED_TOPIC: StringName = &"observe_action_started"' in player_source, "F22 observe start event missing")
    require('OBSERVE_CANCELLED_TOPIC: StringName = &"observe_action_cancelled"' in player_source, "F22 observe cancel event missing")
    require('OBSERVE_SINGLE_PRESS: StringName = &"SINGLE_PRESS"' in player_source, "single-press observe mode missing")
    require("remap_action_to_physical_key" in player_source, "semantic remap implementation missing")
    require("set_camera_fov_degrees" in player_source, "FOV control implementation missing")
    require("set_look_inversion" in player_source, "look inversion implementation missing")
    require("target_position" not in ui_source.lower(), "UI source exposes target-position channel")
    require("raw_hidden" not in ui_source.lower(), "UI source exposes raw hidden-state channel")
    require("refresh_control_prompt" in ui_source, "remapped prompt update implementation missing")

    require("collision_layer = 2" in scene_source, "player scene collision layer drift")
    require("collision_mask = 1" in scene_source, "player scene collision mask drift")
    require("floor_constant_speed = true" in scene_source, "player floor constant-speed assumption missing")
    require("floor_max_angle = 0.7853982" in scene_source, "player floor max-angle assumption missing")
    require("floor_snap_length = 0.1" in scene_source, "player floor snap assumption missing")

    print("VEILWILD_F18_CONTRACT_VALID")
    print(json.dumps({
        "contractSha256": sha256(CONTRACT),
        "playerScriptSha256": sha256(PLAYER),
        "uiScriptSha256": sha256(UI),
        "playerSceneSha256": sha256(PLAYER_SCENE),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
