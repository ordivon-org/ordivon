from __future__ import annotations

from dataclasses import asdict, dataclass


DETECTOR_FAMILIES = frozenset({"CF02", "CF03", "CF04", "CF05", "CF06", "CF07", "CF08"})
REPAIR_ROUTES = {
    "CF02": "network/provider-path",
    "CF03": "http-request-presentation",
    "CF04": "browser-launch-js-presentation",
    "CF05": "automation-control-layer",
    "CF06": "cross-layer-consistency",
    "CF07": "profile-session-lifecycle",
    "CF08": "provider-policy-drift-attribution-only",
}


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def _digest(value: object, label: str) -> str:
    text = _required_text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise ValueError(f"{label} must be one sha256 digest")
    try:
        int(text[7:], 16)
    except ValueError as error:
        raise ValueError(f"{label} must be one sha256 digest") from error
    return text


@dataclass(frozen=True, slots=True)
class DetectorObservation:
    detector_id: str
    family: str
    detector_version: str
    observation_digest: str
    coverage: str

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "DetectorObservation":
        expected = {"detectorId", "family", "detectorVersion", "observationDigest", "coverage"}
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("detector observation must contain exactly the canonical fields")
        family = _required_text(value["family"], "family")
        if family not in DETECTOR_FAMILIES:
            raise ValueError(f"unsupported browser-security detector family: {family}")
        return cls(
            detector_id=_required_text(value["detectorId"], "detectorId"),
            family=family,
            detector_version=_required_text(value["detectorVersion"], "detectorVersion"),
            observation_digest=_digest(value["observationDigest"], "observationDigest"),
            coverage=_required_text(value["coverage"], "coverage"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "detectorId": self.detector_id,
            "family": self.family,
            "detectorVersion": self.detector_version,
            "observationDigest": self.observation_digest,
            "coverage": self.coverage,
        }


@dataclass(frozen=True, slots=True)
class BrowserSecurityWitness:
    witness_id: str
    browser_binary_digest: str
    control_layer_digest: str
    network_authority_digest: str
    observations: tuple[DetectorObservation, ...]
    challenge_standing: str | None = None
    protected_challenge_used_as_detector_oracle: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "BrowserSecurityWitness":
        expected = {
            "schemaVersion",
            "witnessId",
            "browserBinaryDigest",
            "controlLayerDigest",
            "networkAuthorityDigest",
            "observations",
            "challengeStanding",
            "protectedChallengeUsedAsDetectorOracle",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("browser-security witness must contain exactly the canonical fields")
        if value["schemaVersion"] != 1:
            raise ValueError("schemaVersion=1 required")
        oracle = value["protectedChallengeUsedAsDetectorOracle"]
        if oracle is not False:
            raise ValueError("protected challenge outcome cannot be used as a detector oracle")
        raw = value["observations"]
        if not isinstance(raw, list) or not raw:
            raise ValueError("at least one detector observation is required")
        observations = tuple(DetectorObservation.from_dict(row) for row in raw)
        ids = [row.detector_id for row in observations]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate detectorId in browser-security witness")
        standing = value["challengeStanding"]
        if standing is not None:
            standing = _required_text(standing, "challengeStanding")
        return cls(
            witness_id=_required_text(value["witnessId"], "witnessId"),
            browser_binary_digest=_digest(value["browserBinaryDigest"], "browserBinaryDigest"),
            control_layer_digest=_digest(value["controlLayerDigest"], "controlLayerDigest"),
            network_authority_digest=_digest(value["networkAuthorityDigest"], "networkAuthorityDigest"),
            observations=observations,
            challenge_standing=standing,
            protected_challenge_used_as_detector_oracle=False,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "witnessId": self.witness_id,
            "browserBinaryDigest": self.browser_binary_digest,
            "controlLayerDigest": self.control_layer_digest,
            "networkAuthorityDigest": self.network_authority_digest,
            "observations": [row.to_dict() for row in self.observations],
            "challengeStanding": self.challenge_standing,
            "protectedChallengeUsedAsDetectorOracle": False,
        }

    def observation_map(self) -> dict[str, DetectorObservation]:
        return {row.detector_id: row for row in self.observations}


def compare_browser_security_witnesses(
    baseline: BrowserSecurityWitness, candidate: BrowserSecurityWitness
) -> dict[str, object]:
    before = baseline.observation_map()
    after = candidate.observation_map()
    rows: list[dict[str, object]] = []
    changed_families: set[str] = set()
    detector_drift: set[str] = set()

    for detector_id in sorted(set(before) | set(after)):
        left = before.get(detector_id)
        right = after.get(detector_id)
        if left is None:
            rows.append({"detectorId": detector_id, "status": "ADDED", "family": right.family})
            continue
        if right is None:
            rows.append({"detectorId": detector_id, "status": "MISSING", "family": left.family})
            continue
        if left.family != right.family:
            raise ValueError(f"detector family changed for {detector_id}")
        if left.detector_version != right.detector_version:
            detector_drift.add(detector_id)
            rows.append(
                {
                    "detectorId": detector_id,
                    "family": left.family,
                    "status": "DETECTOR_DRIFT",
                    "baselineVersion": left.detector_version,
                    "candidateVersion": right.detector_version,
                }
            )
            continue
        status = "UNCHANGED" if left.observation_digest == right.observation_digest else "CHANGED"
        if status == "CHANGED":
            changed_families.add(left.family)
        rows.append({"detectorId": detector_id, "family": left.family, "status": status})

    infrastructure_changes = {
        "browserBinary": baseline.browser_binary_digest != candidate.browser_binary_digest,
        "controlLayer": baseline.control_layer_digest != candidate.control_layer_digest,
        "networkAuthority": baseline.network_authority_digest != candidate.network_authority_digest,
    }

    return {
        "schemaVersion": 1,
        "baselineWitnessId": baseline.witness_id,
        "candidateWitnessId": candidate.witness_id,
        "infrastructureChanges": infrastructure_changes,
        "detectors": rows,
        "changedFamilies": sorted(changed_families),
        "detectorDrift": sorted(detector_drift),
        "repairRoutes": [REPAIR_ROUTES[f] for f in sorted(changed_families)],
        "challengeStandingChanged": baseline.challenge_standing != candidate.challenge_standing,
        "rootCauseEstablished": False,
    }
