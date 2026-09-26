"""Infrastructure-only evaluator fixture. R2SELFTEST is not an R2 semantic candidate slot."""
from __future__ import annotations
import copy

MANIFEST = {
    "schemaVersion": 1,
    "candidateId": "R2SELFTEST",
    "humanSignalUsed": False,
    "sourceLineage": {"reusesR1Candidate": False, "reusesExcludedWholeProduct": False},
    "descriptors": {
        "agencyMode": "temporal",
        "improvementCarrier": "execution-skill",
        "consequenceHorizon": "short-loop",
        "failureValue": "skill"
    },
    "implementationCarrier": "web-ts",
    "loopSignature": ["observe", "choose", "execute", "compare", "retry"],
    "mechanismFamilies": [1, 3, 5],
    "causalCouplings": ["choice-to-motion", "motion-to-goal", "failure-to-retry"],
    "actionIds": ["left", "right", "inspect"],
    "adapter": {
        "deterministic": True,
        "contextCount": 4,
        "actionCount": 3,
        "observationFieldCount": 3,
        "playerFacingRuleCount": 3,
        "uiModeCount": 1,
        "maxEpisodeDecisions": 12,
        "maxReachableStatesPerSeed": 256,
        "policyIdentityVisible": False,
        "candidateRewardExposed": False
    }
}


class Game:
    def __init__(self, seed: int, context: int):
        self.seed = seed
        self.context = context
        self.pos = 0
        self.steps = 0
        self.hinted = False
        self._status = "ONGOING"

    def observe(self):
        return {"pos": self.pos, "hinted": self.hinted, "contextParity": self.context % 2}

    def full_state(self):
        return {"seed": self.seed, "context": self.context, "pos": self.pos, "steps": self.steps, "hinted": self.hinted, "status": self._status}

    def legal_actions(self):
        return ["left", "right", "inspect"] if self._status == "ONGOING" else []

    def step(self, action: str):
        if self._status != "ONGOING":
            return
        self.steps += 1
        if action == "right":
            self.pos += 1
        elif action == "left":
            self.pos = max(0, self.pos - 1)
        elif action == "inspect":
            self.hinted = True
        else:
            raise ValueError(action)
        target = 3 + (self.context % 2)
        if self.pos >= target:
            self._status = "WIN"
        elif self.steps >= 12:
            self._status = "LOSS"

    def status(self):
        return self._status

    def clone(self):
        return copy.deepcopy(self)


def create_game(seed: int, context: int):
    return Game(seed, context)
