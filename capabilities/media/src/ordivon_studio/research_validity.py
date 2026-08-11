from __future__ import annotations

import hashlib
import json
import math
import random
import sqlite3
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable, Mapping, Sequence

from .grounded_meaning import canonical_digest


OUTCOME_ROLES = ("primary", "guardrail", "secondary", "exploratory")
EVENT_TYPES = (
    "trial.proposed",
    "trial.duplicate",
    "trial.rejected",
    "trial.failed",
    "trial.evaluated",
    "trial.selected",
    "trial.holdout_revealed",
)
NORMAL = NormalDist()


def seed_commitment(seed: str) -> str:
    if not isinstance(seed, str) or not seed:
        raise ValueError("seed must be a non-empty string")
    return "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _seed_int(seed: str, namespace: str) -> int:
    digest = hashlib.sha256(f"{seed}\x00{namespace}".encode("utf-8")).digest()
    return int.from_bytes(digest[:16], "big")


def _rng(seed: str, namespace: str) -> random.Random:
    return random.Random(_seed_int(seed, namespace))


def one_sided_p(z: float) -> float:
    return max(0.0, min(1.0, 1.0 - NORMAL.cdf(float(z))))


def _strict_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def validate_registration(value: Mapping[str, Any]) -> dict[str, Any]:
    registration = dict(value)
    if registration.get("schemaVersion") != 1 or registration.get("kind") != "ordivon.studio.creative-alpha-experiment":
        raise ValueError("unsupported Creative Alpha experiment registration")
    _strict_text(registration.get("experimentId"), "experimentId")
    _strict_text(registration.get("hypothesis"), "hypothesis")
    _strict_text(registration.get("observerClass"), "observerClass")
    encounter = registration.get("encounter")
    if not isinstance(encounter, dict) or not encounter:
        raise ValueError("encounter must be a non-empty object")
    outcomes = registration.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise ValueError("outcomes must be a non-empty array")
    seen: set[str] = set()
    primary_count = 0
    for raw in outcomes:
        if not isinstance(raw, dict):
            raise ValueError("outcome must be an object")
        outcome_id = _strict_text(raw.get("outcomeId"), "outcomeId")
        if outcome_id in seen:
            raise ValueError(f"duplicate outcomeId: {outcome_id}")
        seen.add(outcome_id)
        role = raw.get("role")
        if role not in OUTCOME_ROLES:
            raise ValueError(f"unsupported outcome role: {role}")
        primary_count += int(role == "primary")
        _strict_text(raw.get("measure"), "outcome measure")
    if primary_count != 1:
        raise ValueError("exactly one primary outcome is required in R6 v0")
    search = registration.get("search")
    if not isinstance(search, dict):
        raise ValueError("search must be an object")
    if search.get("mode") not in {"static", "adaptive"}:
        raise ValueError("search mode must be static or adaptive")
    budget = search.get("attemptBudget")
    if not isinstance(budget, int) or budget < 2:
        raise ValueError("search attemptBudget must be >= 2")
    _strict_text(search.get("visibleSeed"), "visible search seed")
    stop_rule = registration.get("stopRule")
    if stop_rule != {"kind": "fixed-attempt-budget", "attemptBudget": budget}:
        raise ValueError("R6 v0 requires a fixed attempt-budget stop rule")
    holdout = registration.get("holdout")
    if not isinstance(holdout, dict) or holdout.get("status") != "sealed":
        raise ValueError("holdout must begin sealed")
    commitment = holdout.get("seedCommitment")
    if not isinstance(commitment, str) or not commitment.startswith("sha256:") or len(commitment) != 71:
        raise ValueError("holdout seed commitment must be a SHA-256 identity")
    if "seed" in holdout or "holdoutSeed" in holdout:
        raise ValueError("registration must not contain the holdout seed")
    digest = registration.get("registrationDigest")
    semantic = {key: item for key, item in registration.items() if key != "registrationDigest"}
    expected = canonical_digest(semantic)
    if digest is not None and digest != expected:
        raise ValueError("registration digest mismatch")
    registration["registrationDigest"] = expected
    return registration


def build_null_registration(
    *,
    mode: str,
    attempt_budget: int,
    visible_seed: str,
    holdout_seed_commitment: str,
    experiment_id: str | None = None,
) -> dict[str, Any]:
    experiment_id = experiment_id or f"experiment:studio:r6a:null-search:{mode}"
    registration: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-experiment",
        "experimentId": experiment_id,
        "hypothesis": (
            "In a universe whose true creative intervention effect is exactly zero, high-budget search can manufacture an impressive visible winner, "
            "but complete search accounting, a replayed search null, and an independently sealed holdout should prevent that winner from becoming Creative Alpha evidence."
        ),
        "observerClass": "synthetic-null-observer",
        "encounter": {
            "kind": "synthetic-controlled-encounter",
            "trueCreativeAlpha": 0.0,
            "interpretation": "The modeled observation is a standardized adaptation-consequence estimate under a known zero-effect data-generating process.",
        },
        "outcomes": [
            {
                "outcomeId": "adaptation-effect-z",
                "role": "primary",
                "measure": "standardized estimated incremental adaptation consequence; higher is the searched direction",
            },
            {
                "outcomeId": "holdout-effect-z",
                "role": "guardrail",
                "measure": "independent standardized effect for the frozen candidate after holdout reveal",
            },
            {
                "outcomeId": "search-corrected-p",
                "role": "secondary",
                "measure": "empirical tail probability of the selected visible statistic under replay of the same full search procedure",
            },
            {
                "outcomeId": "visible-winner-effect",
                "role": "exploratory",
                "measure": "naive selected visible effect retained to expose best-of-N inflation, never as confirmatory evidence",
            },
        ],
        "search": {
            "mode": mode,
            "attemptBudget": int(attempt_budget),
            "visibleSeed": visible_seed,
            "searchIsData": True,
        },
        "stopRule": {"kind": "fixed-attempt-budget", "attemptBudget": int(attempt_budget)},
        "holdout": {
            "status": "sealed",
            "seedCommitment": holdout_seed_commitment,
            "revealLaw": "The raw holdout seed is absent from registration and search execution. It may be supplied only after winner freeze, and any reveal contaminates that holdout for future tuning.",
        },
        "decisionLaw": (
            "A large visible winner is not Creative Alpha. R6-A succeeds when search inflation is visible, search-aware false-positive calibration remains controlled, "
            "and the frozen candidate does not acquire confirmatory support merely from being the best result of the search."
        ),
    }
    registration["registrationDigest"] = canonical_digest(registration)
    return validate_registration(registration)


class TrialLedger:
    """Append-only, hash-chained search history for one Studio experiment.

    This is deliberately local R6 equipment. Finance has an independently evolved consumer with
    nearly the same research need; R6 does not prematurely move either implementation into a
    shared repository before the repeated-consumer boundary is demonstrated by practice.
    """

    def __init__(self, path: str | Path, *, search_id: str):
        self.path = Path(path)
        self.search_id = _strict_text(search_id, "search_id")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS trial_events (
              seq INTEGER PRIMARY KEY AUTOINCREMENT,
              event_id TEXT NOT NULL UNIQUE,
              search_id TEXT NOT NULL,
              attempt_id TEXT NOT NULL,
              candidate_id TEXT NOT NULL,
              event_type TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              prev_hash TEXT,
              event_hash TEXT NOT NULL UNIQUE
            )
            """
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS trial_events_search_idx ON trial_events(search_id,seq)")
        self.db.execute(
            "CREATE TRIGGER IF NOT EXISTS trial_events_no_update BEFORE UPDATE ON trial_events "
            "BEGIN SELECT RAISE(ABORT,'trial events are append-only'); END"
        )
        self.db.execute(
            "CREATE TRIGGER IF NOT EXISTS trial_events_no_delete BEFORE DELETE ON trial_events "
            "BEGIN SELECT RAISE(ABORT,'trial events are append-only'); END"
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def _last_hash(self) -> str | None:
        row = self.db.execute(
            "SELECT event_hash FROM trial_events WHERE search_id=? ORDER BY seq DESC LIMIT 1", (self.search_id,)
        ).fetchone()
        return str(row[0]) if row else None

    def append(self, attempt_id: str, candidate_id: str, event_type: str, payload: Mapping[str, Any]) -> str:
        _strict_text(attempt_id, "attempt_id")
        _strict_text(candidate_id, "candidate_id")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported trial event type: {event_type}")
        previous = self._last_hash()
        semantic = {
            "searchId": self.search_id,
            "attemptId": attempt_id,
            "candidateId": candidate_id,
            "eventType": event_type,
            "payload": dict(payload),
            "prevHash": previous,
        }
        event_hash = canonical_digest(semantic)
        event_id = "trial-event://" + event_hash.removeprefix("sha256:")
        self.db.execute(
            "INSERT INTO trial_events(event_id,search_id,attempt_id,candidate_id,event_type,payload_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?)",
            (
                event_id,
                self.search_id,
                attempt_id,
                candidate_id,
                event_type,
                json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                previous,
                event_hash,
            ),
        )
        self.db.commit()
        return event_id

    def verify(self) -> bool:
        previous: str | None = None
        rows = self.db.execute(
            "SELECT attempt_id,candidate_id,event_type,payload_json,prev_hash,event_hash FROM trial_events WHERE search_id=? ORDER BY seq",
            (self.search_id,),
        )
        for attempt_id, candidate_id, event_type, payload_json, observed_prev, observed_hash in rows:
            if observed_prev != previous:
                return False
            semantic = {
                "searchId": self.search_id,
                "attemptId": attempt_id,
                "candidateId": candidate_id,
                "eventType": event_type,
                "payload": json.loads(payload_json),
                "prevHash": previous,
            }
            if canonical_digest(semantic) != observed_hash:
                return False
            previous = observed_hash
        return True

    def summary(self) -> dict[str, Any]:
        event_counts = {
            str(row[0]): int(row[1])
            for row in self.db.execute(
                "SELECT event_type,count(*) FROM trial_events WHERE search_id=? GROUP BY event_type", (self.search_id,)
            )
        }
        attempts = int(
            self.db.execute(
                "SELECT count(DISTINCT attempt_id) FROM trial_events WHERE search_id=?", (self.search_id,)
            ).fetchone()[0]
        )
        candidates = int(
            self.db.execute(
                "SELECT count(DISTINCT candidate_id) FROM trial_events WHERE search_id=? AND event_type='trial.proposed'",
                (self.search_id,),
            ).fetchone()[0]
        )
        return {
            "searchId": self.search_id,
            "attemptCount": attempts,
            "uniqueCandidateCount": candidates,
            "eventCounts": event_counts,
            "eventChainValid": self.verify(),
        }


def candidate_identity(config: Mapping[str, Any]) -> str:
    return "creative-candidate://" + canonical_digest(dict(config)).removeprefix("sha256:")


def _record(
    ledger: TrialLedger | None,
    *,
    sequence: int,
    candidate_id: str,
    event_type: str,
    payload: Mapping[str, Any],
) -> None:
    if ledger is not None:
        ledger.append(
            f"trial-attempt://{ledger.search_id.rsplit(':', 1)[-1]}/{sequence:06d}",
            candidate_id,
            event_type,
            payload,
        )


def _static_search_stat(seed: str, budget: int, ledger: TrialLedger | None = None) -> dict[str, Any]:
    rng = _rng(seed, "static-visible-search")
    winner: dict[str, Any] | None = None
    for sequence in range(1, budget + 1):
        config = {"family": "independent-expression-probe", "sequence": sequence}
        candidate_id = candidate_identity(config)
        _record(ledger, sequence=sequence, candidate_id=candidate_id, event_type="trial.proposed", payload={"config": config})
        z = rng.gauss(0.0, 1.0)
        result = {
            "candidateId": candidate_id,
            "config": config,
            "visibleStatisticZ": z,
            "visibleEstimatedDelta": z * 0.10,
            "standardError": 0.10,
        }
        _record(
            ledger,
            sequence=sequence,
            candidate_id=candidate_id,
            event_type="trial.evaluated",
            payload={"visibleStatisticZ": z, "visibleEstimatedDelta": z * 0.10, "standardError": 0.10},
        )
        if winner is None or z > float(winner["visibleStatisticZ"]):
            winner = result
    assert winner is not None
    return winner


def _adaptive_search_stat(seed: str, budget: int, ledger: TrialLedger | None = None) -> dict[str, Any]:
    rng = _rng(seed, "adaptive-visible-search")
    family_count = min(16, max(2, budget // 8))
    rho = 0.60
    shared_scale = math.sqrt(rho)
    idiosyncratic_scale = math.sqrt(1.0 - rho)
    family_latent = {family: rng.gauss(0.0, shared_scale) for family in range(family_count)}
    family_sums = {family: 0.0 for family in range(family_count)}
    family_counts = {family: 0 for family in range(family_count)}
    family_branches = {family: 0 for family in range(family_count)}
    winner: dict[str, Any] | None = None

    for sequence in range(1, budget + 1):
        if sequence <= family_count:
            family = sequence - 1
        else:
            if rng.random() < 0.82:
                family = max(
                    range(family_count),
                    key=lambda item: family_sums[item] / family_counts[item] if family_counts[item] else float("-inf"),
                )
            else:
                family = rng.randrange(family_count)
        family_branches[family] += 1
        config = {
            "family": "adaptive-expression-family",
            "familyId": family,
            "branch": family_branches[family],
            "selectionPolicy": "running-family-mean-82pct-exploit",
        }
        candidate_id = candidate_identity(config)
        _record(ledger, sequence=sequence, candidate_id=candidate_id, event_type="trial.proposed", payload={"config": config})
        z = family_latent[family] + rng.gauss(0.0, idiosyncratic_scale)
        family_sums[family] += z
        family_counts[family] += 1
        result = {
            "candidateId": candidate_id,
            "config": config,
            "visibleStatisticZ": z,
            "visibleEstimatedDelta": z * 0.10,
            "standardError": 0.10,
        }
        _record(
            ledger,
            sequence=sequence,
            candidate_id=candidate_id,
            event_type="trial.evaluated",
            payload={
                "visibleStatisticZ": z,
                "visibleEstimatedDelta": z * 0.10,
                "standardError": 0.10,
                "familyRunningMean": family_sums[family] / family_counts[family],
            },
        )
        if winner is None or z > float(winner["visibleStatisticZ"]):
            winner = result
    assert winner is not None
    winner["searchDiagnostics"] = {
        "familyCount": family_count,
        "withinVisibleFamilyCorrelation": rho,
        "attemptsByFamily": {str(key): value for key, value in family_counts.items()},
    }
    return winner


def run_registered_search(registration: Mapping[str, Any], ledger: TrialLedger | None = None) -> dict[str, Any]:
    registered = validate_registration(registration)
    search = registered["search"]
    mode = str(search["mode"])
    budget = int(search["attemptBudget"])
    visible_seed = str(search["visibleSeed"])
    if mode == "static":
        winner = _static_search_stat(visible_seed, budget, ledger)
    else:
        winner = _adaptive_search_stat(visible_seed, budget, ledger)
    winner.update(
        {
            "schemaVersion": 1,
            "kind": "ordivon.studio.creative-alpha-winner-freeze",
            "experimentId": registered["experimentId"],
            "registrationDigest": registered["registrationDigest"],
            "searchMode": mode,
            "attemptBudget": budget,
            "naiveOneSidedP": one_sided_p(float(winner["visibleStatisticZ"])),
            "holdoutStatus": "sealed-not-observed",
        }
    )
    if ledger is not None:
        _record(
            ledger,
            sequence=budget + 1,
            candidate_id=str(winner["candidateId"]),
            event_type="trial.selected",
            payload={
                "visibleStatisticZ": winner["visibleStatisticZ"],
                "naiveOneSidedP": winner["naiveOneSidedP"],
                "attemptBudget": budget,
            },
        )
        winner["trialLedger"] = ledger.summary()
    winner["winnerDigest"] = canonical_digest({key: value for key, value in winner.items() if key != "winnerDigest"})
    return winner


def _winner_stat_for_replay(mode: str, budget: int, seed: str) -> float:
    if mode == "static":
        return float(_static_search_stat(seed, budget)["visibleStatisticZ"])
    if mode == "adaptive":
        return float(_adaptive_search_stat(seed, budget)["visibleStatisticZ"])
    raise ValueError(mode)


def empirical_tail_probability(observed: float, reference: Sequence[float]) -> float:
    if not reference:
        raise ValueError("reference distribution is empty")
    exceed = sum(value >= observed for value in reference)
    return (exceed + 1.0) / (len(reference) + 1.0)


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    ordered = sorted(values)
    position = q * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    weight = position - low
    return float(ordered[low] * (1.0 - weight) + ordered[high] * weight)


def search_replay_correction(
    registration: Mapping[str, Any],
    winner: Mapping[str, Any],
    *,
    replay_seed: str,
    replay_count: int = 2000,
) -> dict[str, Any]:
    registered = validate_registration(registration)
    if winner.get("registrationDigest") != registered["registrationDigest"]:
        raise ValueError("winner is not bound to this registration")
    if replay_count < 100:
        raise ValueError("replay_count must be >= 100")
    mode = str(registered["search"]["mode"])
    budget = int(registered["search"]["attemptBudget"])
    maxima = [
        _winner_stat_for_replay(mode, budget, f"{replay_seed}:{index:06d}")
        for index in range(1, replay_count + 1)
    ]
    observed = float(winner["visibleStatisticZ"])
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-search-replay-correction",
        "experimentId": registered["experimentId"],
        "registrationDigest": registered["registrationDigest"],
        "winnerDigest": winner["winnerDigest"],
        "searchMode": mode,
        "attemptBudget": budget,
        "replayCount": replay_count,
        "observedWinnerZ": observed,
        "naiveOneSidedP": one_sided_p(observed),
        "searchCorrectedP": empirical_tail_probability(observed, maxima),
        "nullMaxSummary": {
            "mean": sum(maxima) / len(maxima),
            "p50": _quantile(maxima, 0.50),
            "p95": _quantile(maxima, 0.95),
            "p99": _quantile(maxima, 0.99),
            "maximum": max(maxima),
        },
        "interpretationLaw": "The reference distribution replays the same complete search procedure in zero-effect worlds. It corrects winner selection, not the outcome scale itself.",
    }
    result["correctionDigest"] = canonical_digest(result)
    return result


def evaluate_sealed_holdout(
    registration: Mapping[str, Any],
    winner: Mapping[str, Any],
    *,
    holdout_seed: str,
    ledger: TrialLedger | None = None,
) -> dict[str, Any]:
    registered = validate_registration(registration)
    if winner.get("registrationDigest") != registered["registrationDigest"]:
        raise ValueError("winner is not bound to this registration")
    if seed_commitment(holdout_seed) != registered["holdout"]["seedCommitment"]:
        raise ValueError("holdout seed does not satisfy the sealed commitment")
    candidate_id = str(winner["candidateId"])
    rng = _rng(holdout_seed, f"holdout:{candidate_id}")
    z = rng.gauss(0.0, 1.0)
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-holdout-result",
        "experimentId": registered["experimentId"],
        "registrationDigest": registered["registrationDigest"],
        "winnerDigest": winner["winnerDigest"],
        "candidateId": candidate_id,
        "holdoutSeedCommitment": registered["holdout"]["seedCommitment"],
        "holdoutStatisticZ": z,
        "holdoutEstimatedDelta": z * 0.10,
        "standardError": 0.10,
        "holdoutOneSidedP": one_sided_p(z),
        "trueCreativeAlpha": 0.0,
        "holdoutStatus": "revealed-contaminated-for-future-tuning",
        "interpretationLaw": "This holdout is independent of visible search and is evidence only for the already-frozen candidate. Its raw seed was not present in registration or search execution.",
    }
    if ledger is not None:
        budget = int(registered["search"]["attemptBudget"])
        _record(
            ledger,
            sequence=budget + 2,
            candidate_id=candidate_id,
            event_type="trial.holdout_revealed",
            payload={
                "holdoutStatisticZ": z,
                "holdoutOneSidedP": result["holdoutOneSidedP"],
                "holdoutSeedCommitment": result["holdoutSeedCommitment"],
            },
        )
        result["trialLedger"] = ledger.summary()
    result["holdoutDigest"] = canonical_digest(result)
    return result


def calibration_experiment(
    *,
    mode: str,
    budgets: Iterable[int],
    worlds: int = 400,
    reference_replays: int = 1600,
    seed: str = "r6a-calibration-20260811",
    alpha: float = 0.05,
) -> dict[str, Any]:
    if mode not in {"static", "adaptive"}:
        raise ValueError("mode must be static or adaptive")
    if worlds < 100 or reference_replays < 400:
        raise ValueError("calibration requires >=100 worlds and >=400 reference replays")
    rows: dict[str, Any] = {}
    for budget in budgets:
        budget = int(budget)
        reference = [
            _winner_stat_for_replay(mode, budget, f"{seed}:reference:{budget}:{index:06d}")
            for index in range(1, reference_replays + 1)
        ]
        naive_false = 0
        corrected_false = 0
        holdout_false = 0
        dual_evidence_false_promotion = 0
        observed_maxima: list[float] = []
        holdout_zs: list[float] = []
        for index in range(1, worlds + 1):
            observed = _winner_stat_for_replay(mode, budget, f"{seed}:world:{budget}:{index:06d}")
            holdout = _rng(seed, f"holdout-calibration:{mode}:{budget}:{index:06d}").gauss(0.0, 1.0)
            observed_maxima.append(observed)
            holdout_zs.append(holdout)
            naive_p = one_sided_p(observed)
            corrected_p = empirical_tail_probability(observed, reference)
            holdout_p = one_sided_p(holdout)
            naive_false += int(naive_p < alpha)
            corrected_false += int(corrected_p < alpha)
            holdout_false += int(holdout_p < alpha)
            dual_evidence_false_promotion += int(corrected_p < alpha and holdout_p < alpha)
        rows[str(budget)] = {
            "attemptBudget": budget,
            "worldCount": worlds,
            "referenceReplayCount": reference_replays,
            "naiveFalsePositiveRate": naive_false / worlds,
            "searchCorrectedFalsePositiveRate": corrected_false / worlds,
            "sealedHoldoutFalsePositiveRate": holdout_false / worlds,
            "dualEvidenceFalsePromotionRate": dual_evidence_false_promotion / worlds,
            "meanSelectedVisibleZ": sum(observed_maxima) / worlds,
            "p95SelectedVisibleZ": _quantile(observed_maxima, 0.95),
            "meanHoldoutZ": sum(holdout_zs) / worlds,
            "referenceNullMaxP95": _quantile(reference, 0.95),
        }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-null-calibration",
        "mode": mode,
        "alpha": alpha,
        "trueCreativeAlpha": 0.0,
        "rows": rows,
        "interpretationLaw": (
            "Naive false-positive rate measures the invalid practice of treating the best searched candidate as if it were preregistered. "
            "Search-corrected rate uses the full search-replay null. Holdout rate evaluates an independent frozen-candidate observation. "
            "Dual-evidence false promotion requires both independent evidence classes to cross the preregistered alpha threshold; it is the R6-A3 promotion gate, not a retroactive rescore of R6-A1/A2."
        ),
    }
    result["calibrationDigest"] = canonical_digest(result)
    return result


def score_null_attack(
    *,
    registration: Mapping[str, Any],
    winner: Mapping[str, Any],
    correction: Mapping[str, Any],
    holdout: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> dict[str, Any]:
    registered = validate_registration(registration)
    digest = registered["registrationDigest"]
    if any(item.get("registrationDigest") != digest for item in (winner, correction, holdout)):
        raise ValueError("R6-A artifacts do not share one registration")
    rows = calibration.get("rows")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("calibration rows missing")
    largest_budget = str(max(int(key) for key in rows))
    largest = rows[largest_budget]
    corrected_rates = [float(row["searchCorrectedFalsePositiveRate"]) for row in rows.values()]
    holdout_rates = [float(row["sealedHoldoutFalsePositiveRate"]) for row in rows.values()]
    signals = {
        "visibleWinnerLooksNaivelySignificant": float(winner["naiveOneSidedP"]) < 0.05,
        "officialSearchCorrectionRejectsFalseAlpha": float(correction["searchCorrectedP"]) >= 0.05,
        "officialSealedHoldoutRejectsFalseAlpha": float(holdout["holdoutOneSidedP"]) >= 0.05,
        "highBudgetNaiveFalsePositiveInflation": float(largest["naiveFalsePositiveRate"]) >= 0.95,
        "searchCorrectionCalibrated": all(0.015 <= rate <= 0.085 for rate in corrected_rates),
        "sealedHoldoutCalibrated": all(0.015 <= rate <= 0.085 for rate in holdout_rates),
        "holdoutWasIndependentOfVisibleWinner": abs(float(largest["meanHoldoutZ"])) <= 0.20,
    }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-r6a-score",
        "experimentId": registered["experimentId"],
        "registrationDigest": digest,
        "acceptanceSignals": signals,
        "accepted": all(signals.values()),
        "observed": {
            "visibleWinnerZ": winner["visibleStatisticZ"],
            "visibleWinnerNaiveP": winner["naiveOneSidedP"],
            "searchCorrectedP": correction["searchCorrectedP"],
            "holdoutZ": holdout["holdoutStatisticZ"],
            "holdoutP": holdout["holdoutOneSidedP"],
            "calibrationMode": calibration.get("mode"),
            "largestBudgetCalibration": largest,
        },
        "decisionLaw": (
            "Passing R6-A means the apparatus exposes selection inflation while maintaining calibrated search-aware and sealed-holdout evidence under a known zero-effect universe. "
            "It does not establish any positive creative law."
        ),
    }
    result["scoreDigest"] = canonical_digest(result)
    return result
