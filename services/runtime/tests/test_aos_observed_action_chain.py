from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts" / "governance"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import observe_action  # noqa: E402
import verify_observed_action_chain as chain  # noqa: E402


FIXTURE_DIR = ROOT / "examples" / "aos" / "ai-action-declaration-dogfood"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def base_observation() -> dict:
    observed = load_fixture("observed.match.json")
    for key in ("event_id", "prev_event_hash", "event_hash", "source_identity", "observed_sequence"):
        observed.pop(key, None)
    return observed


def sealed_pair() -> tuple[dict, dict]:
    first = observe_action.seal_observation(base_observation())
    second_base = copy.deepcopy(base_observation())
    second_base["object_id"] = "aos:actions:ObservedAction:create-candidate-rule-dogfood-second"
    second_base["observed_files_modified"] = ["docs/governance/candidate-rule-drafts.jsonl"]
    second = observe_action.seal_observation(
        second_base,
        prev_event_hash=first["event_hash"],
        observed_sequence=2,
    )
    return first, second


def test_observed_action_hash_chain_passes_for_sealed_pair() -> None:
    first, second = sealed_pair()

    findings = chain.verify_chain([(Path("first.json"), first), (Path("second.json"), second)])

    assert findings == []


def test_observed_action_hash_chain_fails_when_payload_tampered() -> None:
    first, second = sealed_pair()
    second["observed_files_modified"].append("docs/governance/document-registry.jsonl")

    findings = chain.verify_chain([(Path("first.json"), first), (Path("second.json"), second)])

    assert len(findings) == 1
    assert any(error.startswith("event_hash_mismatch") for error in findings[0]["errors"])


def test_observed_action_hash_chain_fails_when_previous_hash_breaks() -> None:
    first, second = sealed_pair()
    second = observe_action.seal_observation(
        {key: value for key, value in second.items() if key != "event_hash"},
        prev_event_hash="sha256:" + "0" * 64,
        observed_sequence=2,
    )

    findings = chain.verify_chain([(Path("first.json"), first), (Path("second.json"), second)])

    assert len(findings) == 1
    assert any(error.startswith("prev_event_hash_mismatch") for error in findings[0]["errors"])


def test_observed_action_hash_chain_rejects_ai_written_observation() -> None:
    observed = observe_action.seal_observation(base_observation())
    observed["origin"] = "AI_WRITTEN"
    observed["created_by"] = "codex"
    observed["source_identity"] = "codex"
    observed["provenance"]["collector"] = "ai_agent"
    observed["observation_sources"] = ["AI_WRITTEN:self-report"]
    observed["event_hash"] = observe_action.compute_event_hash(observed)

    findings = chain.verify_chain([(Path("forged.json"), observed)])

    assert len(findings) == 1
    assert any(error.startswith("origin_not_system_observed") for error in findings[0]["errors"])
    assert any(error.startswith("created_by_not_trusted_system") for error in findings[0]["errors"])
