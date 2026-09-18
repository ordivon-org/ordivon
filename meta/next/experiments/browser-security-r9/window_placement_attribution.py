#!/usr/bin/env python3
"""R9 neutral Chromium profile window-placement attribution.

R9 projects only the non-secret browser.window_placement geometry metadata from the production
carrier-11 Chromium Preferences file. It then creates a fresh canary-91 profile containing only a
synthetic Preferences document with that projected placement and measures a neutral data:text/html
page.

The production browser is never connected. No cookies, tokens, history, account data, page content,
or provider session material is projected. The experiment never visits a protected provider,
interacts with a challenge, or crosses SEND.

Run inside /run/netns/nv2-browserless-prod.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
HARNESS_CURRENT = pathlib.Path("/opt/ordivon/agent-automation/current")
HARNESS_SCRIPTS = HARNESS_CURRENT / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from browserless_substrate import BrowserlessPool  # noqa: E402

R3_PATH = ROOT / "experiments/browser-security-r3/neutral_differential.py"
R8_PATH = ROOT / "experiments/browser-security-r8/fresh_service_attribution.py"
CANARY_PATH = HARNESS_SCRIPTS / "browser_security_browserless_canary.py"

PRODUCTION_PREFERENCES = pathlib.Path("/var/lib/ordivon/browserless/11/Default/Preferences")
R8_RUN1 = ROOT / "evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run1-20260918.json"
R8_REPEATABILITY = ROOT / "evidence/browser-security/cloudflare-provider-security-exp-r8-repeatability-20260918.json"
NETWORK_NAMESPACE = "nv2-browserless-prod"
WINDOW_KEYS = (
    "left",
    "top",
    "right",
    "bottom",
    "maximized",
    "work_area_left",
    "work_area_top",
    "work_area_right",
    "work_area_bottom",
)


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


r3 = _load_module("browser_security_r3_neutral_r9", R3_PATH)
r8 = _load_module("browser_security_r8_fresh_r9", R8_PATH)
canary = _load_module("browser_security_canary_r9", CANARY_PATH)


def sha256_file(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require_network_namespace() -> None:
    current = os.stat("/proc/self/ns/net")
    target = os.stat(f"/run/netns/{NETWORK_NAMESPACE}")
    if (current.st_dev, current.st_ino) != (target.st_dev, target.st_ino):
        raise RuntimeError(f"R9 must execute inside Network-v2 namespace {NETWORK_NAMESPACE}")


def project_window_placement(path: pathlib.Path) -> dict[str, int | bool]:
    """Project only allowlisted non-secret window placement metadata."""
    value = json.loads(path.read_text(encoding="utf-8"))
    browser = value.get("browser") if isinstance(value, dict) else None
    placement = browser.get("window_placement") if isinstance(browser, dict) else None
    if not isinstance(placement, dict):
        raise RuntimeError("production profile lacks browser.window_placement")
    out: dict[str, int | bool] = {}
    for key in WINDOW_KEYS:
        if key not in placement:
            raise RuntimeError(f"window placement lacks required field: {key}")
        item = placement[key]
        if key == "maximized":
            if not isinstance(item, bool):
                raise RuntimeError("window placement maximized must be boolean")
        elif not isinstance(item, int) or isinstance(item, bool):
            raise RuntimeError(f"window placement {key} must be integer")
        out[key] = item
    if set(out) != set(WINDOW_KEYS):
        raise RuntimeError("window placement projection shape mismatch")
    return out


def outer_from_placement(value: dict[str, int | bool]) -> list[int]:
    left = value["left"]
    top = value["top"]
    right = value["right"]
    bottom = value["bottom"]
    if not all(isinstance(row, int) and not isinstance(row, bool) for row in (left, top, right, bottom)):
        raise ValueError("window placement coordinates must be integers")
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        raise ValueError("window placement dimensions must be positive")
    return [width, height]


def load_r8_reference() -> tuple[dict[str, Any], str]:
    evidence = json.loads(R8_RUN1.read_text(encoding="utf-8"))
    receipt = json.loads(R8_REPEATABILITY.read_text(encoding="utf-8"))
    actual = sha256_file(R8_RUN1)
    if receipt.get("standing") != "BYTE_IDENTICAL_FRESH_SERVICE_REPEATABILITY":
        raise RuntimeError("R8 reference is not repeatability-qualified")
    if actual != receipt.get("run1", {}).get("sha256"):
        raise RuntimeError("R8 reference digest disagrees with repeatability receipt")
    if evidence.get("safetyBoundary", {}).get("protectedProviderVisited") is not False:
        raise RuntimeError("R8 reference crossed protected-provider boundary")
    return evidence, actual


def write_synthetic_preferences(profile: pathlib.Path, placement: dict[str, int | bool]) -> pathlib.Path:
    default = profile / "Default"
    default.mkdir(parents=True, exist_ok=True)
    target = default / "Preferences"
    target.write_text(
        json.dumps({"browser": {"window_placement": placement}}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(target, 0o600)
    return target


def cleanup_state() -> dict[str, bool]:
    return {
        "containerAbsent": not r8.r7.r5.podman_container_exists(canary.CANARY_CONTAINER),
        "profileAbsent": not canary.CANARY_PROFILE.exists(),
        "xSocketAbsent": not pathlib.Path(f"/tmp/.X11-unix/X{100 + canary.CANARY_INSTANCE}").exists(),
        "xauthAbsent": not canary.CANARY_XAUTH.exists(),
    }


def collect_seeded_fresh_service(
    placement: dict[str, int | bool],
) -> tuple[dict[str, Any], dict[str, object]]:
    canary._require_canary_idle()
    control = canary.discover_production_control()
    r8_reference, _ = load_r8_reference()
    if control["image"] != r8_reference["controls"]["browserlessImage"]:
        raise RuntimeError("current Browserless image drifted from R8 reference")
    if control["networkNamespace"] != r8_reference["controls"]["networkNamespace"]:
        raise RuntimeError("current Network-v2 namespace drifted from R8 reference")

    config = canary._load_production_config(control["networkNamespace"])
    display = None
    arm: dict[str, Any] | None = None
    pre_page_count: int | None = None
    try:
        canary._prepare_profile()
        write_synthetic_preferences(canary.CANARY_PROFILE, placement)
        display = canary._start_display()
        with tempfile.TemporaryDirectory(prefix="ordivon-browser-security-r9-") as tmp:
            config_path = pathlib.Path(tmp) / "config.json"
            config_path.write_text(json.dumps(config, sort_keys=True, indent=2) + "\n")
            canary._start_container(
                image=control["image"],
                namespace=control["networkNamespace"],
                environment=control["environment"],
            )
            canary._wait_healthy(config_path)
            endpoint = BrowserlessPool.from_dict(config["browserSubstrate"]).endpoints[0]

            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(
                    endpoint.authenticated_connection_endpoint(timeout_ms=90_000),
                    timeout=30_000,
                )
                try:
                    if len(browser.contexts) != 1:
                        raise RuntimeError("R9 fresh Browserless requires exactly one context")
                    pre_page_count = len(browser.contexts[0].pages)
                    arm = r3.collect_arm(browser, create_new_page=True)
                finally:
                    browser.close()
    finally:
        canary._stop_container()
        canary._cleanup_profile()
        canary._stop_display(display)

    cleanup = cleanup_state()
    if not all(cleanup.values()):
        raise RuntimeError(f"R9 canary cleanup incomplete: {cleanup}")
    if arm is None or pre_page_count is None:
        raise RuntimeError("R9 seeded fresh-service observation incomplete")
    return arm, {
        "preCollectionPageCount": pre_page_count,
        "cleanup": cleanup,
        "image": control["image"],
        "networkNamespace": control["networkNamespace"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    require_network_namespace()

    r8_reference, r8_sha = load_r8_reference()
    placement = project_window_placement(PRODUCTION_PREFERENCES)
    production_outer = r8_reference["comparisons"]["freshServiceToProductionReference"]["rightGeometry"]["outer"]
    if outer_from_placement(placement) != production_outer:
        raise RuntimeError("profile window placement does not match frozen production outer geometry")

    seeded_arm, metadata = collect_seeded_fresh_service(placement)
    fresh_baseline = r8_reference["freshService"]["arm"]
    synthetic_preferences = {"browser": {"window_placement": placement}}

    output = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-neutral-window-placement-r9",
        "date": "2026-09-18",
        "standing": "NEUTRAL_WINDOW_PLACEMENT_CAUSAL_ATTRIBUTION_ROOT_CAUSE_OPEN",
        "safetyBoundary": {
            "protectedProviderVisited": False,
            "challengeInteracted": False,
            "cookieValuesRead": False,
            "providerSendAttempted": False,
            "productionBrowserConnected": False,
            "productionProfileCopied": False,
            "projectedProductionProfileFields": list(WINDOW_KEYS),
        },
        "reference": {
            "r8Run1Path": str(R8_RUN1.relative_to(ROOT)),
            "r8Run1Sha256": r8_sha,
            "r8Standing": r8_reference["standing"],
        },
        "productionWindowPlacementProjection": placement,
        "productionOuterReference": production_outer,
        "syntheticProfile": {
            "preferences": synthetic_preferences,
            "containsProductionCredentialsOrSessionData": False,
        },
        "seededFreshService": {
            "preCollectionPageCount": metadata["preCollectionPageCount"],
            "arm": seeded_arm,
            "cleanup": metadata["cleanup"],
        },
        "comparisons": {
            "r8FreshBaselineToSeededFresh": r8.r7.pair_summary(fresh_baseline, seeded_arm),
        },
        "mechanismCheck": {
            "projectedPlacementOuter": outer_from_placement(placement),
            "seededObservedOuter": seeded_arm["page"]["windowOuter"],
            "productionReferenceOuter": production_outer,
            "outerReproducedExactly": (
                seeded_arm["page"]["windowOuter"]
                == outer_from_placement(placement)
                == production_outer
            ),
            "innerViewportPreserved": (
                seeded_arm["page"]["windowInner"]
                == fresh_baseline["page"]["windowInner"]
                == [800, 600]
            ),
            "targetTopologyPreserved": (
                seeded_arm["browser"]["targetTypeCounts"]
                == fresh_baseline["browser"]["targetTypeCounts"]
                == {"page": 2}
            ),
        },
        "interpretationGuard": {
            "providerCausalityEstablished": False,
            "rootCauseEstablished": False,
            "challengeOutcomeUsedAsDetectorOracle": False,
            "note": (
                "Synthetic window-placement sufficiency localizes the measured production outer-window "
                "geometry to Chromium profile-restored window state. It does not explain how that state "
                "was historically created or establish provider relevance."
            ),
        },
    }
    if not output["mechanismCheck"]["outerReproducedExactly"]:
        raise RuntimeError("synthetic window placement did not reproduce production outer geometry")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "productionWindowPlacementProjection": placement,
                "mechanismCheck": output["mechanismCheck"],
                "comparison": output["comparisons"]["r8FreshBaselineToSeededFresh"],
                "cleanup": metadata["cleanup"],
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
