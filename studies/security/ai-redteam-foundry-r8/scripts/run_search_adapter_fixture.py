from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (
    ROOT,
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r4",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r7",
):
    sys.path.insert(0, str(path))

from foundry.providers import PyritScenarioResultsAdapter  # noqa: E402
from foundry_r4 import ExperimentEnvironmentSpec, IsolationVector, ResourceBudget, SandboxProviderBinding, canonical_digest  # noqa: E402
from foundry_r7 import SyntheticWorldObserver  # noqa: E402
from foundry_r8 import SearchBudget, SearchControl, bind_search_run, normalize_provider_batch  # noqa: E402

D = lambda c: "sha256:" + c * 64

observer_digest = canonical_digest(SyntheticWorldObserver.binding.to_dict())
environment = ExperimentEnvironmentSpec(
    environment_id="env:r8-fixture",
    threat_class="synthetic_agent",
    base_image_digest=D("a"),
    synthetic_world_digest=D("b"),
    tool_surface_digest=D("c"),
    observer_spec_digest=observer_digest,
    isolation=IsolationVector("separate_process_tree", "shared", "synthetic", "none", "synthetic_only", "none", "synthetic_only", "resettable", "independent"),
    budget=ResourceBudget(60, 30, 512, 128, 32, 0),
    provider=SandboxProviderBinding("synthetic-r5", "r5", "synthetic_world", D("d")),
)
run = bind_search_run(
    search_id="search:r8-fixture",
    provider="pyrit",
    provider_version="synthetic-fixture-v1",
    provider_engine="scenario-results-attacks",
    provider_run_id="pyrit-run:r8-fixture",
    target_id="target:r8-fixture",
    environment=environment,
    observer_binding=SyntheticWorldObserver.binding,
    seed_artifact_digest=D("e"),
    provider_config_digest=D("f"),
    budget=SearchBudget(8, 4, 32, 60000),
    control=SearchControl(42, "provider_adaptive", "provider:pyrit-scorer"),
)
fixture = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1" / "fixtures" / "pyrit" / "scenario-results-attacks.synthetic.json"
rows = PyritScenarioResultsAdapter("synthetic-fixture-v1").parse_bytes(
    fixture.read_bytes(),
    str(fixture.relative_to(REPO_ROOT)),
    scenario_result_id=run.provider_run_id,
    target_id=run.target_id,
)
results = normalize_provider_batch(run, rows)
print(json.dumps({
    "schema": "ordivon.ai-redteam.r8-search-adapter-fixture",
    "run": run.to_dict(),
    "runDigest": run.digest,
    "resultCount": len(results),
    "results": [item.to_dict() for item in results],
    "securityEvidenceRefs": [item.candidate.artifact_ref.to_security_evidence_ref_projection() for item in results],
}, sort_keys=True, indent=2))
