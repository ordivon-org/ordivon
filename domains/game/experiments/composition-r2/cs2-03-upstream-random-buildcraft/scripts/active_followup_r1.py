#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(__file__).with_name('computational_player_science_r1.py')
spec = importlib.util.spec_from_file_location('cps', MODULE_PATH)
cps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cps)

SURR = json.loads((ROOT / 'evidence' / 'player-effect-surrogate-r1.json').read_text())
TOP = SURR['activeExperimentSelection']['topCandidates'][:8]
observed = []
for row in TOP:
    actual = cps.evaluate_profile(row['params'], 7000 + row['rank'], reps=12)
    observed.append({
        'rank': row['rank'],
        'params': row['params'],
        'expectedInformationGainNats': row['expectedInformationGainNats'],
        'surrogatePredictedScoreATE': row['surrogatePredictedScoreATE'],
        'directSimulatedScoreATE': actual,
        'predictionError': actual - row['surrogatePredictedScoreATE'],
        'absolutePredictionError': abs(actual - row['surrogatePredictedScoreATE']),
    })

out = {
    'schemaVersion': 1,
    'kind': 'cs2-03-active-player-model-followup-r1',
    'selectionSourceStanding': SURR['standing'],
    'criterion': SURR['activeExperimentSelection']['criterion'],
    'selectedCount': len(observed),
    'directReplicatesPerSequence': 12,
    'encounterSequencesPerProfile': len(cps.ESEQS),
    'observations': observed,
    'meanAbsolutePredictionError': float(np.mean([x['absolutePredictionError'] for x in observed])),
    'maxAbsolutePredictionError': float(np.max([x['absolutePredictionError'] for x in observed])),
    'signMismatchCount': int(sum(np.sign(x['surrogatePredictedScoreATE']) != np.sign(x['directSimulatedScoreATE']) for x in observed)),
    'standing': 'ACTIVE_FOLLOWUP_EXECUTED',
    'interpretation': 'High-information player-model points were selected by the current surrogate, then evaluated by direct paired simulation. Large prediction errors are evidence against surrogate adequacy, not evidence against the underlying mechanism simulator.',
    'boundary': 'This is sequential computational model evaluation inside the declared synthetic player envelope. It is not Human calibration.'
}
(ROOT / 'evidence' / 'active-player-model-followup-r1.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
