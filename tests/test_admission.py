import unittest

from ordivon_security_v2.admission import ReplayBinding, canonical_digest


class AdmissionTests(unittest.TestCase):
    def test_canonical_digest_is_order_independent_for_object_keys(self) -> None:
        self.assertEqual(canonical_digest({"a": 1, "b": 2}), canonical_digest({"b": 2, "a": 1}))

    def test_exact_replay_returns_original_admission(self) -> None:
        binding = ReplayBinding()
        request = {"requestId": "range-effect-request:1", "value": 1}
        admission = {"admitted": True, "reason": "admitted"}
        first, replayed = binding.bind(request=request, admission=admission)
        self.assertFalse(replayed)
        second, replayed = binding.bind(request=dict(request), admission={"admitted": False})
        self.assertTrue(replayed)
        self.assertEqual(first, second)

    def test_changed_content_under_same_identity_fails_closed(self) -> None:
        binding = ReplayBinding()
        binding.bind(
            request={"requestId": "range-effect-request:1", "value": 1},
            admission={"admitted": True},
        )
        with self.assertRaisesRegex(ValueError, "reused with different content"):
            binding.bind(
                request={"requestId": "range-effect-request:1", "value": 2},
                admission={"admitted": True},
            )


if __name__ == "__main__":
    unittest.main()
