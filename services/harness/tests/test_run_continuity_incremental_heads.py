"""Pure replay-differential test for hot incremental and cold full Journal folding."""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from ordivon_harness.ordivon.run_continuity import (
    EventSourcedRunContinuity,
    _PROVIDER_CLEAR_EVENT_KINDS,
    _PROVIDER_EVENT_KINDS,
    _TOOL_EVENT_KINDS,
)


class _Journal:
    def __init__(self):
        self.events = []
        self.after_sequences = []

    def load_run(self, run_id):
        assert run_id == "harness-run:incremental-test"
        return SimpleNamespace(revision=len(self.events))

    def list_run_events(self, run_id, *, after_sequence=0):
        assert run_id == "harness-run:incremental-test"
        self.after_sequences.append(after_sequence)
        return tuple(e for e in self.events if e.sequence > after_sequence)

    def append(self, kind, **data):
        seq = len(self.events) + 1
        event = SimpleNamespace(
            sequence=seq,
            run_revision=seq,
            event_kind=kind,
            data=data,
            event_id=f"event:incremental:{seq}",
        )
        self.events.append(event)
        return event


def _continuity(store):
    continuity = EventSourcedRunContinuity.__new__(EventSourcedRunContinuity)
    continuity.store = store
    continuity.harness_run_id = "harness-run:incremental-test"
    continuity._heads_cache = None
    continuity._heads_cache_last_sequence = 0
    return continuity


def _full_fold(events):
    result = {"provider": None, "tool": None, "snapshot": None, "working_set": None}
    for event in events:
        if event.event_kind in _PROVIDER_CLEAR_EVENT_KINDS:
            result["provider"] = None
        if event.event_kind in _PROVIDER_EVENT_KINDS:
            result["provider"] = event
        if event.event_kind in _TOOL_EVENT_KINDS:
            result["tool"] = event
        if "snapshotObjectDigest" in event.data:
            result["snapshot"] = event
        if event.event_kind == "harness.working-set-recorded":
            result["working_set"] = event
    return result


class IncrementalHeadsTests(unittest.TestCase):
    def test_hot_tail_and_cold_full_match_on_provider_clear_tool_unknown_and_snapshot(self):
        store = _Journal()
        hot = _continuity(store)
        kinds = [
            ("harness.provider-call-claimed", {}),
            ("harness.provider-call-dispatching", {}),
            ("harness.provider-call-unknown", {}),
            ("harness.tool-step-prepared", {}),
            ("harness.snapshot-recorded", {"snapshotObjectDigest": "sha256:" + "a" * 64}),
            ("harness.provider-call-completed", {}),
            ("harness.working-set-recorded", {"committed": False}),
            ("harness.working-set-recorded", {"committed": True}),
            ("harness.provider-call-claimed", {}),
            ("harness.run-paused", {}),
            ("harness.provider-call-claimed", {}),
            ("harness.provider-call-unknown", {}),
            ("harness.trace-recorded", {}),
        ]
        for kind, data in kinds:
            store.append(kind, **data)
            heads = hot._heads()
            cold = _continuity(store)._heads()
            expected = _full_fold(store.events)
            for key, event in expected.items():
                self.assertIs(getattr(heads, key), event)
                self.assertIs(getattr(cold, key), event)
            self.assertEqual(
                store.after_sequences[-2], store.events[-2].sequence if len(store.events) > 1 else 0
            )
            self.assertEqual(store.after_sequences[-1], 0)
            self.assertIs(hot._heads(), heads)
        self.assertEqual(hot._heads().provider.event_kind, "harness.provider-call-unknown")
        self.assertEqual(hot._heads().tool.event_kind, "harness.tool-step-prepared")
        self.assertEqual(hot._heads().working_set.data, {"committed": True})


if __name__ == "__main__":
    unittest.main()
