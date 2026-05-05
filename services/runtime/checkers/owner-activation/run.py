"""Owner Activation Gate — Policy activation requires named Owner + signoff.

Validates that any attempt to activate a Policy (to active_shadow or
active_enforced) has:
  1. A named owner (PolicyRecord.owner is not None)
  2. Owner signoff in policy-activation-ledger.jsonl
  3. The signoff comes from the declared owner (not someone else)

Rust RFC FCP pattern: individual ❌ can block.
Ordivon translation: activation requires the specific Owner's ✅.
"""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.policies.models import PolicyRecord, PolicyState

ACTIVATION_LEDGER = ROOT / "docs" / "governance" / "policy-activation-ledger.jsonl"


@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _load_activation_signoffs() -> dict[str, list[dict]]:
    """Load activation signoffs, keyed by policy_id."""
    signoffs: dict[str, list[dict]] = {}
    if not ACTIVATION_LEDGER.exists():
        return signoffs
    with open(ACTIVATION_LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                pid = entry.get("policy_id", "")
                if pid not in signoffs:
                    signoffs[pid] = []
                signoffs[pid].append(entry)
            except json.JSONDecodeError:
                pass
    return signoffs


def validate_activation(policy_id: str, policy_state: str,
                        owner_id: str | None,
                        signoffs: dict[str, list[dict]]) -> list[str]:
    """Validate that policy activation has proper owner signoff.

    Returns list of violations (empty = valid).
    """
    violations = []

    # Only check activation-relevant states
    if policy_state not in ("active_shadow", "active_enforced"):
        return violations

    # Gate 1: Owner must exist
    if not owner_id:
        violations.append(
            f"{policy_id}: state='{policy_state}' but no owner assigned. "
            f"Activation requires a named owner. "
            f"Set PolicyRecord.owner before activating."
        )
        return violations

    # Gate 2: Owner must have signed off
    policy_signoffs = signoffs.get(policy_id, [])
    owner_signoffs = [s for s in policy_signoffs if s.get("owner_id") == owner_id]

    if not owner_signoffs:
        violations.append(
            f"{policy_id}: state='{policy_state}' but owner '{owner_id}' "
            f"has not signed off in policy-activation-ledger.jsonl. "
            f"Activation requires explicit owner approval."
        )
        return violations

    # Gate 3: Most recent signoff must be an approval
    latest = max(owner_signoffs, key=lambda s: s.get("timestamp", ""))
    action = latest.get("action", "")
    if action not in ("approve", "activate"):
        violations.append(
            f"{policy_id}: owner '{owner_id}' most recent action is "
            f"'{action}' (not 'approve'/'activate'). "
            f"Activation requires explicit approval."
        )

    return violations


def run() -> CheckerResult:
    findings = []
    stats = {"policies_checked": 0, "activation_attempts": 0, "violations": 0}

    signoffs = _load_activation_signoffs()

    # Scan for PolicyRecords in candidate-rule-drafts.jsonl
    # and any policy-activation-ledger.jsonl entries
    drafts_file = ROOT / "docs" / "governance" / "candidate-rule-drafts.jsonl"

    if drafts_file.exists():
        with open(drafts_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    draft = json.loads(line)
                except json.JSONDecodeError:
                    continue

                policy_id = draft.get("candidate_rule_id", "")
                review_status = draft.get("review_status", "")

                # A draft being promoted to Policy would be "accepted_candidate"
                status = draft.get("status", "")
                if status == "accepted_candidate":
                    stats["policies_checked"] += 1
                    stats["activation_attempts"] += 1

                    # Accepted candidates should have an owner set
                    # (For now, check: does the draft have an explicit owner?)
                    owner = draft.get("owner", None)
                    violations = validate_activation(
                        policy_id, "active_shadow", owner, signoffs
                    )
                    if violations:
                        stats["violations"] += len(violations)
                        findings.extend(violations)

    # Also check the shadow-evaluation-log for policies being shadow-tested
    shadow_log = ROOT / "docs" / "governance" / "shadow-evaluation-log.jsonl"
    if shadow_log.exists():
        active_shadow_candidates = set()
        with open(shadow_log) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    readiness = entry.get("readiness", {})
                    if readiness.get("level") == "ready_for_activation_review":
                        active_shadow_candidates.add(entry.get("candidate_rule_id", ""))
                except json.JSONDecodeError:
                    pass

        for cid in active_shadow_candidates:
            stats["policies_checked"] += 1
            # Shadow-evaluated candidates need owner before activation
            owner = None  # would come from the candidate rule draft
            violations = validate_activation(cid, "active_shadow", owner, signoffs)
            if violations:
                stats["violations"] += len(violations)
                findings.extend(violations)

    if findings:
        findings.append(
            f"Owner activation violations: {stats['violations']}. "
            f"Activation requires named owner + explicit signoff."
        )

    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        dict(stats),
    )


if __name__ == "__main__":
    r = run()
    print(f"Policies checked: {r.stats.get('policies_checked', 0)}")
    for f in r.findings:
        print(f"  {f}")
    sys.exit(r.exit_code)
