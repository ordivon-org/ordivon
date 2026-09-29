#!/usr/bin/env python3
"""R8 neutral fresh-Browserless-service attribution for Browser Security.

R8 reuses the production canary-91 lifecycle to start the current immutable Browserless image
with a fresh empty profile, the production Network-v2 namespace/environment, and isolated Xvfb.
It then measures only a neutral data:text/html page and compares that fresh service observation to
the frozen R7 launcher-matched direct arm and frozen R7 production Browserless arm.

The experiment never visits ChatGPT or another protected provider, never interacts with a
challenge, never reads cookie values, and never crosses SEND. Execute it inside
/run/netns/nv2-browserless-prod so the canary loopback endpoint resolves to the intended namespace.
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
HARNESS_CURRENT = pathlib.Path(
    os.environ.get("ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT", "/opt/ordivon/agent-automation/current")
)
HARNESS_SCRIPTS = HARNESS_CURRENT / 'scripts'
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from browserless_substrate import BrowserlessPool  # noqa: E402

R3_PATH = ROOT / 'experiments/browser-security-r3/neutral_differential.py'
R7_PATH = ROOT / 'experiments/browser-security-r7/launcher_default_ablation.py'
CANARY_PATH = HARNESS_SCRIPTS / 'browser_security_browserless_canary.py'


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load module: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


r3 = _load_module('browser_security_r3_neutral_r8', R3_PATH)
r7 = _load_module('browser_security_r7_launcher_r8', R7_PATH)
canary = _load_module('browser_security_canary_r8', CANARY_PATH)

R7_RUN1 = ROOT / 'evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run1-20260918.json'
R7_REPEATABILITY = ROOT / 'evidence/browser-security/cloudflare-provider-security-exp-r7-repeatability-20260918.json'


NETWORK_NAMESPACE = 'nv2-browserless-prod'


def require_network_namespace() -> None:
    current = os.stat('/proc/self/ns/net')
    target = os.stat(f'/run/netns/{NETWORK_NAMESPACE}')
    if (current.st_dev, current.st_ino) != (target.st_dev, target.st_ino):
        raise RuntimeError(
            f'R8 must execute inside Network-v2 namespace {NETWORK_NAMESPACE}'
        )


def sha256_file(path: pathlib.Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def load_r7_reference() -> tuple[dict[str, Any], str]:
    evidence = json.loads(R7_RUN1.read_text(encoding='utf-8'))
    receipt = json.loads(R7_REPEATABILITY.read_text(encoding='utf-8'))
    actual = sha256_file(R7_RUN1)
    expected = receipt.get('run1', {}).get('sha256')
    if actual != expected:
        raise RuntimeError('R7 reference digest disagrees with repeatability receipt')
    if receipt.get('standing') != 'BYTE_IDENTICAL_CONTROLLED_REPEATABILITY':
        raise RuntimeError('R7 reference is not repeatability-qualified')
    if evidence.get('safetyBoundary', {}).get('protectedProviderVisited') is not False:
        raise RuntimeError('R7 reference crossed protected-provider boundary')
    return evidence, actual


def _fresh_cleanup_state() -> dict[str, bool]:
    return {
        'containerAbsent': not r7.r5.podman_container_exists(canary.CANARY_CONTAINER),
        'profileAbsent': not canary.CANARY_PROFILE.exists(),
        'xSocketAbsent': not pathlib.Path(f'/tmp/.X11-unix/X{100 + canary.CANARY_INSTANCE}').exists(),
        'xauthAbsent': not canary.CANARY_XAUTH.exists(),
    }


def collect_fresh_browserless() -> tuple[dict[str, Any], dict[str, object]]:
    canary._require_canary_idle()
    control = canary.discover_production_control()
    r7_reference, _ = load_r7_reference()
    if control['image'] != r7_reference['controls']['browserlessImage']:
        raise RuntimeError('current Browserless image drifted from R7 reference')
    if control['networkNamespace'] != r7_reference['controls']['networkNamespace']:
        raise RuntimeError('current Network-v2 namespace drifted from R7 reference')

    config = canary._load_production_config(control['networkNamespace'])
    display = None
    pre_page_count: int | None = None
    fresh_arm: dict[str, Any] | None = None
    chromium_digest: str | None = None
    with tempfile.TemporaryDirectory(prefix='ordivon-browser-security-r8-') as tmp:
        config_path = pathlib.Path(tmp) / 'canary-config.json'
        config_path.write_text(json.dumps(config, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        try:
            canary._prepare_profile()
            display = canary._start_display()
            canary._start_container(
                image=control['image'],
                namespace=control['networkNamespace'],
                environment=control['environment'],
            )
            canary._wait_healthy(config_path)
            chromium_digest = r3.browserless_binary_digest(canary.CANARY_CONTAINER)
            endpoint = BrowserlessPool.from_dict(config['browserSubstrate']).endpoints[0]

            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(
                    endpoint.authenticated_connection_endpoint(timeout_ms=90_000),
                    timeout=30_000,
                )
                try:
                    if len(browser.contexts) != 1:
                        raise RuntimeError('R8 fresh Browserless requires exactly one context')
                    pre_page_count = len(browser.contexts[0].pages)
                    fresh_arm = r3.collect_arm(browser, create_new_page=True)
                finally:
                    browser.close()
        finally:
            canary._stop_container()
            canary._cleanup_profile()
            canary._stop_display(display)

    cleanup = _fresh_cleanup_state()
    if not all(cleanup.values()):
        raise RuntimeError(f'R8 canary cleanup incomplete: {cleanup}')
    if fresh_arm is None or chromium_digest is None or pre_page_count is None:
        raise RuntimeError('R8 fresh Browserless observation incomplete')
    return fresh_arm, {
        'preCollectionPageCount': pre_page_count,
        'chromiumDigest': chromium_digest,
        'cleanup': cleanup,
        'image': control['image'],
        'networkNamespace': control['networkNamespace'],
        'presentationEnvironment': {
            key: control['environment'][key]
            for key in ('TZ',)
            if key in control['environment']
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    require_network_namespace()

    r7_reference, r7_sha = load_r7_reference()
    launcher_reference = r7_reference['arms']['containerDirectLauncherMatched']
    production_reference = r7_reference['arms']['browserlessCurrent']

    fresh_arm, fresh_meta = collect_fresh_browserless()
    if fresh_meta['chromiumDigest'] != r7_reference['controls']['chromiumDigest']:
        raise RuntimeError('fresh Browserless Chromium digest drifted from R7 reference')

    output = {
        'schemaVersion': 1,
        'kind': 'ordivon.browser-security-neutral-fresh-service-r8',
        'date': '2026-09-18',
        'standing': 'NEUTRAL_FRESH_SERVICE_ATTRIBUTION_ONLY_ROOT_CAUSE_OPEN',
        'safetyBoundary': {
            'protectedProviderVisited': False,
            'challengeInteracted': False,
            'cookieValuesRead': False,
            'providerSendAttempted': False,
            'productionBrowserConnected': False,
        },
        'reference': {
            'r7Run1Path': str(R7_RUN1.relative_to(ROOT)),
            'r7Run1Sha256': r7_sha,
            'r7Standing': r7_reference['standing'],
        },
        'controls': {
            'browserlessImage': fresh_meta['image'],
            'chromiumDigest': fresh_meta['chromiumDigest'],
            'networkNamespace': fresh_meta['networkNamespace'],
            'neutralPage': 'data:text/html',
            'freshProfile': True,
            'productionBrowserConnected': False,
        },
        'freshService': {
            'preCollectionPageCount': fresh_meta['preCollectionPageCount'],
            'arm': fresh_arm,
            'cleanup': fresh_meta['cleanup'],
        },
        'comparisons': {
            'launcherMatchedToFreshService': r7.pair_summary(launcher_reference, fresh_arm),
            'freshServiceToProductionReference': r7.pair_summary(fresh_arm, production_reference),
        },
        'interpretationGuard': {
            'providerCausalityEstablished': False,
            'rootCauseEstablished': False,
            'challengeOutcomeUsedAsDetectorOracle': False,
            'note': (
                'Fresh-service equality localizes a residual to Browserless service/control; '
                'fresh-vs-production differences localize persistent/open-page state only descriptively.'
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    print(json.dumps({
        'preCollectionPageCount': fresh_meta['preCollectionPageCount'],
        'comparisons': output['comparisons'],
        'cleanup': fresh_meta['cleanup'],
    }, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
