#!/usr/bin/env python3
"""CS2-03 Computational Player Science R1.

Combines procedural personas, paired counterfactual simulation, persona-balanced
causal estimands, bootstrap uncertainty, a Bayesian polynomial surrogate,
global permutation sensitivity, and expected-information-gain selection of the
next synthetic player-model experiment.

The outputs are computational evidence about the declared player-model envelope.
They do not claim a calibrated Human population or Human subjective experience.
"""
from __future__ import annotations

import itertools
import json
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "design.json").read_text())
POP = json.loads((ROOT / "model" / "player-population-r1.json").read_text())
MEAS = json.loads((ROOT / "model" / "player-value-measurement-r1.json").read_text())
CARD = D["cards"]
OFFERS = D["offers"]
ENC = D["encounters"]
SYNERGY = D["synergies"]
DIM = len(D["dimensions"])
ENCOUNTER_IDS = list(ENC)
ENCOUNTER_WEIGHTS = np.array([ENC[e]["weights"] for e in ENCOUNTER_IDS], dtype=float)
PRIOR_WEIGHTS = ENCOUNTER_WEIGHTS.mean(axis=0)
PATHS = list(itertools.product(*OFFERS))
ESEQS = list(itertools.product(ENCOUNTER_IDS, repeat=len(OFFERS)))
PARAMS = ["infoUse", "foresight", "riskAversion", "synergyBias", "balanceBias", "habitBias", "temperature"]
BOUNDS = np.array([[POP["parameters"][p]["min"], POP["parameters"][p]["max"]] for p in PARAMS], dtype=float)


def add(a, b):
    return np.asarray(a, dtype=float) + np.asarray(b, dtype=float)


@lru_cache(maxsize=None)
def _build_vector_cached(path):
    v = np.zeros(DIM, dtype=float)
    for c in path:
        v += np.asarray(CARD[c]["stats"], dtype=float)
    for a, b in itertools.combinations(path, 2):
        key = {a, b}
        for s in SYNERGY:
            if set(s["cards"]) == key:
                v += np.asarray(s["bonus"], dtype=float)
    return v


def build_vector(path):
    return _build_vector_cached(tuple(path))


@lru_cache(maxsize=None)
def _synergy_gain_cached(path):
    raw = np.zeros(DIM, dtype=float)
    for c in path:
        raw += np.asarray(CARD[c]["stats"], dtype=float)
    return float(np.sum(build_vector(path) - raw))


def synergy_gain(path):
    return _synergy_gain_cached(tuple(path))


@lru_cache(maxsize=None)
def path_static_features(path):
    path = tuple(path)
    v = build_vector(path)
    across = ENCOUNTER_WEIGHTS @ v
    balance = float(np.min(v))
    syn = synergy_gain(path)
    habit = 0.0
    if len(path) > 1:
        prev = build_vector(path[:-1])
        if np.any(prev > 0):
            dominant = int(np.argmax(prev))
            habit = float(np.asarray(CARD[path[-1]]["stats"], dtype=float)[dominant])
    return v, float(v @ PRIOR_WEIGHTS), float(np.std(across)), balance, syn, habit


def score_path(path, encounters):
    total = 0.0
    for i, e in enumerate(encounters):
        total += float(build_vector(path[: i + 1]) @ np.asarray(ENC[e]["weights"], dtype=float))
    return total


OPTIMAL_SCORE = {}
for es in ESEQS:
    OPTIMAL_SCORE[es] = max(score_path(p, es) for p in PATHS)


def effective_weights(encounter, condition, info_use):
    if condition == "UPSTREAM":
        actual = np.asarray(ENC[encounter]["weights"], dtype=float)
        return info_use * actual + (1.0 - info_use) * PRIOR_WEIGHTS
    return PRIOR_WEIGHTS


def utility(path, encounter, condition, params, round_index):
    path = tuple(path)
    v, prior_score, risk, balance, syn, habit = path_static_features(path)
    w = effective_weights(encounter, condition, params["infoUse"])
    immediate = float(v @ w)
    remaining = len(OFFERS) - round_index - 1
    future_potential = remaining * prior_score
    return (
        immediate
        + params["foresight"] * 0.45 * future_potential
        - params["riskAversion"] * 0.55 * risk
        + params["synergyBias"] * 1.25 * syn
        + params["balanceBias"] * 0.6 * balance
        + params["habitBias"] * 0.55 * habit
    )


def softmax_choice(items, utilities, temperature, u):
    z = np.asarray(utilities, dtype=float)
    t = max(0.02, float(temperature))
    z = (z - np.max(z)) / t
    p = np.exp(np.clip(z, -50, 50))
    p = p / np.sum(p)
    cdf = np.cumsum(p)
    idx = int(np.searchsorted(cdf, min(float(u), 1.0 - 1e-12), side="right"))
    return items[min(idx, len(items) - 1)]


def run_policy(encounters, condition, params, uniforms):
    path = []
    scores = []
    for i, encounter in enumerate(encounters):
        offer = OFFERS[i]
        if params.get("special") == "random":
            idx = min(int(float(uniforms[i]) * len(offer)), len(offer) - 1)
            choice = offer[idx]
        else:
            utils = [utility(path + [c], encounter, condition, params, i) for c in offer]
            choice = softmax_choice(offer, utils, params["temperature"], uniforms[i])
        path.append(choice)
        scores.append(float(build_vector(path) @ np.asarray(ENC[encounter]["weights"], dtype=float)))
    return tuple(path), float(sum(scores)), scores


def normalized_entropy(counter, possible):
    counts = np.array([counter.get(x, 0) for x in possible], dtype=float)
    if counts.sum() <= 0:
        return 0.0
    p = counts[counts > 0] / counts.sum()
    h = float(-np.sum(p * np.log(p)))
    return h / math.log(len(possible)) if len(possible) > 1 else 0.0


def bootstrap_ci(values, rng, draws=2000, alpha=0.05):
    x = np.asarray(values, dtype=float)
    n = len(x)
    means = np.empty(draws)
    for i in range(draws):
        means[i] = float(np.mean(x[rng.integers(0, n, n)]))
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return [float(lo), float(hi)]


def simulate_persona(persona, persona_index, reps=16):
    seq_effects = np.zeros(len(ESEQS))
    seq_switch = np.zeros(len(ESEQS))
    seq_aleatory = np.zeros(len(ESEQS))
    path_counts = {"UPSTREAM": Counter(), "DOWNSTREAM": Counter()}
    action_counts = {c: [Counter() for _ in OFFERS] for c in ["UPSTREAM", "DOWNSTREAM"]}
    condition_scores = {"UPSTREAM": [], "DOWNSTREAM": []}

    random_cube = np.random.default_rng(104729 * (persona_index + 1)).random((len(ESEQS), reps, len(OFFERS)))
    for si, es in enumerate(ESEQS):
        diffs = []
        switches = []
        for rep in range(reps):
            uniforms = random_cube[si, rep]
            up_path, up_score, _ = run_policy(es, "UPSTREAM", persona, uniforms)
            dn_path, dn_score, _ = run_policy(es, "DOWNSTREAM", persona, uniforms)
            diffs.append(up_score - dn_score)
            switches.append(sum(a != b for a, b in zip(up_path, dn_path)) / len(OFFERS))
            path_counts["UPSTREAM"][up_path] += 1
            path_counts["DOWNSTREAM"][dn_path] += 1
            for r, c in enumerate(up_path):
                action_counts["UPSTREAM"][r][c] += 1
            for r, c in enumerate(dn_path):
                action_counts["DOWNSTREAM"][r][c] += 1
            condition_scores["UPSTREAM"].append(up_score)
            condition_scores["DOWNSTREAM"].append(dn_score)
        seq_effects[si] = float(np.mean(diffs))
        seq_switch[si] = float(np.mean(switches))
        seq_aleatory[si] = float(np.var(diffs, ddof=1)) if len(diffs) > 1 else 0.0

    rng = np.random.default_rng(9001 + persona_index)
    up_entropy = np.mean([normalized_entropy(action_counts["UPSTREAM"][r], OFFERS[r]) for r in range(len(OFFERS))])
    dn_entropy = np.mean([normalized_entropy(action_counts["DOWNSTREAM"][r], OFFERS[r]) for r in range(len(OFFERS))])
    max_paths = len(PATHS)
    return {
        "id": persona["id"],
        "params": {k: persona[k] for k in PARAMS},
        "special": persona.get("special"),
        "pairedScoreATE": float(np.mean(seq_effects)),
        "pairedScoreATE95BootstrapCI": bootstrap_ci(seq_effects, rng),
        "contextResponsiveChoiceRate": float(np.mean(seq_switch)),
        "meanWithinSequenceAleatoryVariance": float(np.mean(seq_aleatory)),
        "betweenSequenceEffectVariance": float(np.var(seq_effects, ddof=1)),
        "upstreamMeanScore": float(np.mean(condition_scores["UPSTREAM"])),
        "downstreamMeanScore": float(np.mean(condition_scores["DOWNSTREAM"])),
        "upstreamChoiceEntropy": float(up_entropy),
        "downstreamChoiceEntropy": float(dn_entropy),
        "upstreamPathDiversity": len(path_counts["UPSTREAM"]) / max_paths,
        "downstreamPathDiversity": len(path_counts["DOWNSTREAM"]) / max_paths,
        "seqEffects": seq_effects,
        "seqSwitch": seq_switch,
    }


def two_stage_persona_balanced_ci(persona_results, rng, draws=3000):
    n_p = len(persona_results)
    boots = np.empty(draws)
    for b in range(draws):
        ids = rng.integers(0, n_p, n_p)
        p_means = []
        for idx in ids:
            seq = persona_results[idx]["seqEffects"]
            sids = rng.integers(0, len(seq), len(seq))
            p_means.append(float(np.mean(seq[sids])))
        boots[b] = float(np.mean(p_means))
    return [float(x) for x in np.quantile(boots, [0.025, 0.975])]


def lhs(n, d, rng):
    out = np.empty((n, d))
    for j in range(d):
        perm = rng.permutation(n)
        out[:, j] = (perm + rng.random(n)) / n
    return out


def unit_to_params(x):
    raw = BOUNDS[:, 0] + x * (BOUNDS[:, 1] - BOUNDS[:, 0])
    return {p: float(v) for p, v in zip(PARAMS, raw)}


def evaluate_profile(params, profile_seed, reps=2):
    effects = []
    random_cube = np.random.default_rng(profile_seed * 1000003).random((len(ESEQS), reps, len(OFFERS)))
    for si, es in enumerate(ESEQS):
        for rep in range(reps):
            uniforms = random_cube[si, rep]
            _, us, _ = run_policy(es, "UPSTREAM", params, uniforms)
            _, ds, _ = run_policy(es, "DOWNSTREAM", params, uniforms)
            effects.append(us - ds)
    return float(np.mean(effects))


def poly_features(x):
    # x is already normalized to [0,1].
    x = np.asarray(x, dtype=float)
    feats = [1.0]
    feats.extend(x.tolist())
    feats.extend((x * x).tolist())
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            feats.append(float(x[i] * x[j]))
    return np.asarray(feats, dtype=float)


def feature_matrix(x):
    return np.vstack([poly_features(row) for row in x])


def fit_bayesian_ridge(x_train, y_train, lam=1e-3):
    phi = feature_matrix(x_train)
    reg = np.eye(phi.shape[1]) * lam
    reg[0, 0] = 0.0
    precision = phi.T @ phi + reg
    inv = np.linalg.pinv(precision)
    beta = inv @ phi.T @ y_train
    resid = y_train - phi @ beta
    dof = max(1, len(y_train) - phi.shape[1])
    sigma2 = max(1e-9, float((resid @ resid) / dof))
    cov = sigma2 * inv
    return beta, cov, sigma2


def predict_surrogate(x, beta):
    return feature_matrix(x) @ beta


def r2_score(y, pred):
    den = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - float(np.sum((y - pred) ** 2)) / den if den > 0 else 1.0


def permutation_importance(x_test, y_test, beta, rng, repeats=64):
    base = float(np.mean((y_test - predict_surrogate(x_test, beta)) ** 2))
    out = {}
    for j, name in enumerate(PARAMS):
        losses = []
        for _ in range(repeats):
            xp = x_test.copy()
            xp[:, j] = rng.permutation(xp[:, j])
            losses.append(float(np.mean((y_test - predict_surrogate(xp, beta)) ** 2)))
        out[name] = max(0.0, float(np.mean(losses) - base))
    total = sum(out.values())
    if total > 0:
        out = {k: v / total for k, v in out.items()}
    return out


def main():
    out_dir = ROOT / "evidence"
    out_dir.mkdir(exist_ok=True)

    personas = POP["personas"]
    results = [simulate_persona(p, i) for i, p in enumerate(personas)]
    persona_means = np.array([r["pairedScoreATE"] for r in results])
    overall = float(np.mean(persona_means))
    ci = two_stage_persona_balanced_ci(results, np.random.default_rng(77123))
    random_result = next(r for r in results if r["id"] == "random-baseline")

    # Continuous model-space surrogate.
    rng = np.random.default_rng(20260914)
    samples = lhs(128, len(PARAMS), rng)
    responses = np.array([evaluate_profile(unit_to_params(x), i + 1) for i, x in enumerate(samples)])
    order = rng.permutation(len(samples))
    train_idx, test_idx = order[:100], order[100:]
    x_train, y_train = samples[train_idx], responses[train_idx]
    x_test, y_test = samples[test_idx], responses[test_idx]
    beta, cov, sigma2 = fit_bayesian_ridge(x_train, y_train)
    test_pred = predict_surrogate(x_test, beta)
    test_r2 = r2_score(y_test, test_pred)
    test_mae = float(np.mean(np.abs(y_test - test_pred)))
    importance = permutation_importance(x_test, y_test, beta, np.random.default_rng(8811))

    # Gaussian-linear expected information gain for one additional synthetic profile.
    candidate_unit = lhs(2048, len(PARAMS), np.random.default_rng(445566))
    phi_c = feature_matrix(candidate_unit)
    epistemic_var = np.einsum("ij,jk,ik->i", phi_c, cov, phi_c)
    eig = 0.5 * np.log1p(np.maximum(epistemic_var, 0.0) / sigma2)
    rank = np.argsort(-eig)[:10]
    active = []
    for k, idx in enumerate(rank, 1):
        active.append({
            "rank": k,
            "expectedInformationGainNats": float(eig[idx]),
            "epistemicPredictiveVariance": float(epistemic_var[idx]),
            "params": unit_to_params(candidate_unit[idx]),
            "surrogatePredictedScoreATE": float(phi_c[idx] @ beta),
        })

    compact_personas = []
    for r in results:
        compact_personas.append({k: v for k, v in r.items() if k not in {"seqEffects", "seqSwitch"}})

    sign_agreement = float(np.mean(persona_means > 0))
    nonrandom = [r for r in results if r["id"] != "random-baseline"]
    nonrandom_means = np.array([r["pairedScoreATE"] for r in nonrandom])
    mechanism_standing = (
        "SUPPORTED_IN_DECLARED_SYNTHETIC_PLAYER_ENVELOPE"
        if ci[0] > 0 and np.mean(nonrandom_means > 0) >= 0.75 and abs(random_result["pairedScoreATE"]) < 1e-9
        else "MIXED_OR_INCONCLUSIVE_IN_DECLARED_SYNTHETIC_PLAYER_ENVELOPE"
    )
    surrogate_standing = "PASS_LOCAL_SURROGATE" if test_r2 >= 0.75 else "WEAK_LOCAL_SURROGATE"

    evidence = {
        "schemaVersion": 1,
        "kind": "cs2-03-computational-player-science-r1",
        "experiment": D["id"],
        "standing": mechanism_standing,
        "estimand": {
            "treatment": "UPSTREAM current-encounter information available before choice",
            "control": "DOWNSTREAM current-encounter information revealed after choice",
            "population": "equal-weighted declared procedural persona families; encounter sequences exhaustively enumerated; stochastic policy draws paired by common random numbers",
            "outcome": "total modeled run score",
            "primary": "persona-balanced paired average treatment effect (UPSTREAM - DOWNSTREAM)",
        },
        "design": {
            "personaFamilies": len(personas),
            "encounterSequences": len(ESEQS),
            "stochasticReplicatesPerSequencePersona": 16,
            "pairedCounterfactual": True,
            "commonRandomNumbers": True,
        },
        "primaryEffect": {
            "personaBalancedScoreATE": overall,
            "twoStageBootstrap95CI": ci,
            "personaEffectSignAgreement": sign_agreement,
            "worstPersonaEffect": float(np.min(persona_means)),
            "bestPersonaEffect": float(np.max(persona_means)),
            "randomBaselineEffect": random_result["pairedScoreATE"],
        },
        "personas": compact_personas,
        "measurementModel": MEAS,
        "uncertaintyDiagnostics": {
            "note": "Diagnostics are distinct variance views, not an asserted additive variance decomposition.",
            "betweenPersonaEffectVariance": float(np.var(persona_means, ddof=1)),
            "meanBetweenSequenceEffectVariance": float(np.mean([r["betweenSequenceEffectVariance"] for r in results])),
            "meanWithinSequenceAleatoryVariance": float(np.mean([r["meanWithinSequenceAleatoryVariance"] for r in results])),
            "humanPopulationCalibrationUncertainty": "UNQUANTIFIED_HIGH_NO_DIRECT_CALIBRATION_IN_R1",
            "modelFormUncertainty": "PARTIALLY_PROBED_BY_PERSONA_HETEROGENEITY_ONLY",
        },
        "claimBoundary": "This result estimates causal performance effects inside the declared synthetic player-model envelope. It does not establish Human enjoyment, felt agency, preference, retention, or population prevalence.",
    }

    surrogate = {
        "schemaVersion": 1,
        "kind": "cs2-03-player-model-effect-surrogate-r1",
        "standing": surrogate_standing,
        "target": "paired total-score ATE of UPSTREAM vs DOWNSTREAM",
        "parameterNames": PARAMS,
        "trainingProfiles": len(train_idx),
        "testProfiles": len(test_idx),
        "testR2": float(test_r2),
        "testMAE": test_mae,
        "residualNoiseVariance": float(sigma2),
        "globalPermutationSensitivity": importance,
        "activeExperimentSelection": {
            "criterion": "Gaussian linear-model one-observation expected information gain = 0.5*log(1 + epistemicVariance/residualNoiseVariance)",
            "candidatePool": len(candidate_unit),
            "topCandidates": active,
            "scope": "next synthetic player-model evaluation inside declared parameter envelope; not a Human study and not yet a cross-candidate mechanism selector",
        },
        "boundary": "The surrogate emulates this computational experiment only. Predictive fit does not calibrate the model to Human Player Value or authorize extrapolation outside the declared parameter bounds.",
    }

    (out_dir / "computational-player-science-r1.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (out_dir / "player-effect-surrogate-r1.json").write_text(json.dumps(surrogate, indent=2) + "\n")

    summary = {
        "standing": mechanism_standing,
        "personaBalancedScoreATE": overall,
        "95CI": ci,
        "signAgreement": sign_agreement,
        "randomBaselineEffect": random_result["pairedScoreATE"],
        "surrogateStanding": surrogate_standing,
        "surrogateTestR2": test_r2,
        "surrogateTestMAE": test_mae,
        "topSensitivity": sorted(importance.items(), key=lambda kv: -kv[1])[:4],
        "nextExperiment": active[0],
    }
    print(json.dumps(summary, indent=2))

    assert abs(random_result["pairedScoreATE"]) < 1e-9, "paired random baseline must be treatment-invariant"
    assert all(np.isfinite([overall, test_r2, test_mae]))
    raise SystemExit(0)


if __name__ == "__main__":
    main()
