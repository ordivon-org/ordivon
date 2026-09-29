#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def digest_bytes(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def study_tree_manifest() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        parts = Path(rel).parts
        if "__pycache__" in parts or rel.startswith("evidence/") or path.suffix == ".pyc":
            continue
        data = path.read_bytes()
        entries.append({"path": rel, "sha256": digest_bytes(data), "byteLength": len(data)})
    return entries


def run_json_script(relative_script: str) -> dict[str, object]:
    output = subprocess.check_output(
        [sys.executable, str(ROOT / relative_script)],
        cwd=REPO_ROOT,
        text=True,
    )
    value = json.loads(output)
    if not isinstance(value, dict):
        raise ValueError(f"{relative_script} must emit one JSON object")
    return value


def main() -> None:
    source_revision = subprocess.check_output(
        ["/usr/bin/git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    manifest = study_tree_manifest()
    manifest_digest = digest_bytes(canonical_bytes(manifest))

    bundle = {
        "schema": "ordivon.ai-redteam.evidence-bundle.r1",
        "standing": "EXPERIMENTAL_STUDY_EVIDENCE_NOT_PRODUCTION_SECURITY_STANDING",
        "sourceRevision": source_revision,
        "studyTreeDigest": manifest_digest,
        "studyTreeManifest": manifest,
        "experiments": {
            "syntheticCore": run_json_script("scripts/run_synthetic_campaign.py"),
            "providerReplay": run_json_script("scripts/run_provider_fixture_replay.py"),
            "agentSurfaces": run_json_script("scripts/run_agent_surface_campaign.py"),
            "abstractSearchFixture": run_json_script("scripts/run_abstract_fuzz_campaign.py"),
        },
        "limitations": [
            "All built-in attacks use synthetic canaries/fake tools/abstract behavior; no third-party system was attacked.",
            "PyRIT, garak, and AgentDojo artifacts are provider-shaped replay fixtures, not claims of live provider execution.",
            "Provider judgments are retained as provider judgments and are not production Security standing.",
            "The abstract search fixture is a deterministic test generator, not a replacement for ClusterFuzzLite/Atheris or mature LLM red-team providers.",
            "The bundle proves deterministic study outputs for this exact source/tree state; it does not prove universal model robustness.",
        ],
    }
    bundle["bundleDigest"] = digest_bytes(canonical_bytes(bundle))

    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path = evidence_dir / "ai-redteam-foundry-r1-evidence.json"
    output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": output_path.relative_to(REPO_ROOT).as_posix(), "bundleDigest": bundle["bundleDigest"], "studyTreeDigest": manifest_digest}, sort_keys=True))


if __name__ == "__main__":
    main()
