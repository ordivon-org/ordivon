"""Generated multi-step evidence graph refinement against a multiset oracle."""
from __future__ import annotations

# The reference state is a multiset of independently declared source roles,
# each marked clean or altered. The implementation only sees native API-shaped
# observations, never the reference labels used by the oracle.
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from monitoring_test_support import _native_target_fixture


@lru_cache(maxsize=1)
def _stateful_source_fixture():
    return _native_target_fixture()


class MonitoringGraphMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.owner, self.declared, self.pools, source = _stateful_source_fixture()
        self.source = source["data"]["activeTargets"]
        self.n = len(self.source)
        self.rows = [(i, "clean") for i in range(self.n)]
        self.missing_pools = set()

    @rule(role=st.integers(min_value=0, max_value=100))
    def omit(self, role):
        self.rows = [row for row in self.rows if row[0] != role % self.n]

    @rule(role=st.integers(min_value=0, max_value=100))
    def add(self, role):
        if len(self.rows) < 2 * self.n:
            self.rows.append((role % self.n, "clean"))

    @rule(slot=st.integers(min_value=0, max_value=100),
          defect=st.sampled_from(("instance", "address", "scheme", "extra", "pool", "path")))
    def alter(self, slot, defect):
        if self.rows:
            pos = slot % len(self.rows)
            self.rows[pos] = (self.rows[pos][0], defect)

    @rule(role=st.integers(min_value=0, max_value=100))
    def repair(self, role):
        i = role % self.n
        self.rows = [row for row in self.rows if row[0] != i] + [(i, "clean")]
        self.missing_pools.discard(i)

    @rule(role=st.integers(min_value=0, max_value=100))
    def lose_pool(self, role):
        self.missing_pools.add(role % self.n)

    @rule()
    def reorder(self):
        self.rows.reverse()

    @rule()
    def restore(self):
        self.rows = [(i, "clean") for i in range(self.n)]
        self.missing_pools.clear()

    @invariant()
    def native_observation_matches_independent_multiset_oracle(self):
        from urllib.parse import urlsplit, urlunsplit

        targets = []
        for i, defect in self.rows:
            target = deepcopy(self.source[i])
            if defect == "instance":
                target["labels"]["instance"] = "foreign"
            elif defect == "address":
                target["discoveredLabels"]["__address__"] = "foreign"
            elif defect == "scheme":
                url = urlsplit(target["scrapeUrl"])
                target["scrapeUrl"] = urlunsplit(url._replace(scheme="https"))
            elif defect == "extra":
                target["scrapeUrl"] += ("&" if "?" in target["scrapeUrl"] else "?") + "foreign="
            elif defect == "pool":
                target["scrapePool"] = "foreign"
            elif defect == "path":
                url = urlsplit(target["scrapeUrl"])
                target["scrapeUrl"] = urlunsplit(url._replace(path="/foreign"))
            targets.append(target)
        omitted = {self.source[i]["scrapePool"] for i in self.missing_pools}
        pools = {"data": {"scrapePools": [
            p for p in self.pools["data"]["scrapePools"] if p not in omitted
        ]}}
        expected = (not self.missing_pools and
                    Counter(self.rows) == Counter((i, "clean") for i in range(self.n)))
        try:
            result = self.owner.verify_active_targets(
                self.declared, pools, {"data": {"activeTargets": targets}})
        except ValueError:
            assert not expected
        else:
            assert expected and result == self.n


TestMonitoringGraphMachine = MonitoringGraphMachine.TestCase
TestMonitoringGraphMachine.settings = settings(
    max_examples=40, stateful_step_count=25, deadline=None,
    derandomize=True, database=None,
)
