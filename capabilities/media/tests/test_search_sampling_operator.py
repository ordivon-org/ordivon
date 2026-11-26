"""Independent search protocol and empirical rank regression tests."""
from __future__ import annotations

import hashlib
import math
import random
import unittest
from itertools import product
from unittest.mock import Mock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_studio.research import search_calibration as calibration
from ordivon_studio.research.search_sampling import search_samples
from ordivon_studio.research.trial_registration import build_null_registration, seed_commitment


def scalar_samples(mode, seed, budget):
    namespace = f"{mode}-visible-search"
    digest = hashlib.sha256(f"{seed}\x00{namespace}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:16], "big"))
    if mode == "static":
        return [(i, None, i, rng.gauss(0.0, 1.0), None) for i in range(1, budget + 1)]
    count = min(16, max(2, budget // 8))
    latent = {i: rng.gauss(0, math.sqrt(.60)) for i in range(count)}
    observations = {i: [] for i in range(count)}
    result = []
    for i in range(1, budget + 1):
        if i <= count:
            family = i - 1
        elif rng.random() < .82:
            # Compute sequential sums independently from the whole observation history.
            family = max(range(count), key=lambda f: _sequential_mean(observations[f]))
        else:
            family = rng.randrange(count)
        z = latent[family] + rng.gauss(0, math.sqrt(1 - .60))
        observations[family].append(z)
        result.append((i, family, len(observations[family]), z,
                       _sequential_mean(observations[family])))
    return result


def _sequential_mean(values):
    if not values:
        return -math.inf
    total = 0.0
    for x in values:
        total += x
    return total / len(values)


class SearchSamplingOperatorTest(unittest.TestCase):
    def test_trial_stream_matches_independent_scalar_oracle(self):
        for mode in ("static", "adaptive"):
            for budget in (1, 2, 8, 16, 24, 127, 128, 129, 1000):
                for seed in ("a", "b", "c", "math-r3-visible"):
                    expected = scalar_samples(mode, seed, budget)
                    actual = list(search_samples(mode, seed, budget))
                    self.assertEqual(actual, expected)
                    self.assertEqual(calibration._winner_stat_for_replay(mode, budget, seed),
                                     max(x[3] for x in expected))

    def test_adaptive_cached_means_preserve_ties_and_leader_decrease(self):
        # Initial family means tie at 2. The first family wins, then its
        # mean drops to 0 and the next greedy draw must select family 1.
        rng = Mock()
        rng.gauss.side_effect = [0., 0., 2., 2., -2., 0.]
        rng.random.return_value = 0.
        with patch("ordivon_studio.research.search_sampling._rng", return_value=rng):
            samples = list(search_samples("adaptive", "forced", 4))
        self.assertEqual([sample.family for sample in samples], [0, 1, 0, 1])
        self.assertEqual([sample.running_mean for sample in samples], [2., 2., 0., 1.])

    @given(
        st.lists(st.integers(-8, 8), min_size=4, max_size=64),
        st.lists(st.booleans(), min_size=1, max_size=64),
        st.lists(st.integers(0, 15), min_size=1, max_size=64),
    )
    @settings(max_examples=250, deadline=None, derandomize=True, database=None)
    def test_generated_adaptive_trajectories_match_history_oracle(self, draws, greedy, explore):
        # Force ties, decreases and exploration rather than relying on random seeds
        # to reach those transitions. The oracle recomputes means from history.
        budget = len(draws)
        count = min(16, max(2, budget // 8))
        choices = [greedy[i % len(greedy)] for i in range(budget - count)]
        exploratory = [explore[i % len(explore)] % count for i in range(budget - count)]
        rng = Mock()
        rng.gauss.side_effect = [0.] * count + draws
        rng.random.side_effect = [0. if choice else .99 for choice in choices]
        rng.randrange.side_effect = [
            family for family, choice in zip(exploratory, choices, strict=True) if not choice
        ]
        with patch("ordivon_studio.research.search_sampling._rng", return_value=rng):
            actual = list(search_samples("adaptive", "forced-property", budget))
        observations = [[] for _ in range(count)]
        expected = []
        for i, z in enumerate(draws):
            if i < count:
                family = i
            elif choices[i - count]:
                family = max(range(count), key=lambda f: _sequential_mean(observations[f]))
            else:
                family = exploratory[i - count]
            observations[family].append(z)
            expected.append((i + 1, family, len(observations[family]), float(z),
                             _sequential_mean(observations[family])))
        self.assertEqual(actual, expected)

    def test_null_replay_never_materializes_candidate_identity(self):
        for mode in ("static", "adaptive"):
            with patch.object(calibration, "candidate_identity", side_effect=AssertionError):
                self.assertEqual(calibration._winner_stat_for_replay(mode, 32, "x"),
                                 max(x[3] for x in scalar_samples(mode, "x", 32)))

    def test_static_replay_does_not_materialize_trial_metadata(self):
        # The visible search still consumes the identical canonical draw stream.
        for budget in (1, 2, 31, 128, 1024):
            expected = max(x[3] for x in scalar_samples("static", "metadata-free", budget))
            with patch("ordivon_studio.research.search_sampling.TrialSample",
                       side_effect=AssertionError("unconsumed trial metadata")):
                self.assertEqual(calibration._winner_stat_for_replay(
                    "static", budget, "metadata-free"), expected)

    def test_rank_partition_matches_inclusive_linear_oracle(self):
        for n in range(1, 6):
            for reference in product((-1., 0., 1.), repeat=n):
                for observed in (-2., -1., -0., .5, 1., 2.):
                    self.assertEqual(calibration._ordered_tail_probability(observed, sorted(reference)),
                                     calibration.empirical_tail_probability(observed, reference))

    def test_pre_reform_consumer_digests(self):
        # Captured from source 63ea15e7 before the replacement, Python 3.15.1.
        expected = {
            "static": (
                "7c7a3f274b41bdd3826978345f2fa247e5108d4c4047a22865940c1a39ab5f93",
                "0af31e1f32b70dc9f14cd076253d84cd7c6dd5738c57a59891c512204c83833e",
                "078c9c8b2731033df514024cd777c4d73f66e5e3fe80de7fcd373eb4adcb1999",
            ),
            "adaptive": (
                "46c96769421f9e04a2ab8ebcc256f7622190b16ae2c38ac8f22bd73899ba3c11",
                "df159d0458e628058a8af998ee27c8eb9aeae14c1630673ca8151b9b49218a6f",
                "32db575272a18d66a046250777d052e816ba5e8eb50d1174803a93b50a362997",
            ),
        }
        for mode, digests in expected.items():
            registration = build_null_registration(
                mode=mode, attempt_budget=32, visible_seed="math-r3-visible",
                holdout_seed_commitment=seed_commitment("math-r3-held"),
                experiment_id="creative-experiment://math-r3-"+mode,
            )
            winner = calibration.run_registered_search(registration)
            correction = calibration.search_replay_correction(
                registration, winner, replay_seed="math-r3-replay", replay_count=100)
            result = calibration.calibration_experiment(
                mode=mode, budgets=[10, 32], worlds=100, reference_replays=400,
                seed="math-r3-calibration")
            self.assertEqual(
                (winner["winnerDigest"], correction["correctionDigest"], result["calibrationDigest"]),
                tuple("sha256:"+x for x in digests),
            )


if __name__ == "__main__":
    unittest.main()
