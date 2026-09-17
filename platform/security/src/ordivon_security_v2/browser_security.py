from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


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
        if left.detector_version != right.detector_version or left.coverage != right.coverage:
            detector_drift.add(detector_id)
            row = {
                "detectorId": detector_id,
                "family": left.family,
                "status": "DETECTOR_DRIFT",
                "baselineVersion": left.detector_version,
                "candidateVersion": right.detector_version,
            }
            if left.coverage != right.coverage:
                row["baselineCoverage"] = left.coverage
                row["candidateCoverage"] = right.coverage
            rows.append(row)
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


_SENSITIVE_PUBLIC_KEYS = frozenset(
    {
        "authorization",
        "cookievalue",
        "password",
        "privatekey",
        "secret",
        "setcookie",
        "token",
        "accesstoken",
        "refreshtoken",
        "clientsecret",
    }
)


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("browser-security observation must be canonical JSON data") from error


def canonical_json_digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _normalized_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _validate_public_observation(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"public observation key at {path} must be text")
            if _normalized_key(key) in _SENSITIVE_PUBLIC_KEYS:
                raise ValueError(f"sensitive field is forbidden in public observation: {path}.{key}")
            _validate_public_observation(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_public_observation(child, f"{path}[{index}]")
        return
    if value is None or isinstance(value, (str, int, float, bool)):
        _canonical_json_bytes(value)
        return
    raise ValueError(f"public observation at {path} must be JSON data")


@dataclass(frozen=True, slots=True)
class BrowserSecurityWitnessBundle:
    witness: BrowserSecurityWitness
    public_observations: tuple[tuple[str, object], ...]

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "BrowserSecurityWitnessBundle":
        expected = {"schemaVersion", "witness", "publicObservations"}
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("browser-security witness bundle must contain exactly the canonical fields")
        if value["schemaVersion"] != 1:
            raise ValueError("schemaVersion=1 required")
        witness_raw = value["witness"]
        if not isinstance(witness_raw, dict):
            raise ValueError("witness must be an object")
        witness = BrowserSecurityWitness.from_dict(witness_raw)
        raw = value["publicObservations"]
        if not isinstance(raw, list):
            raise ValueError("publicObservations must be a list")
        public: list[tuple[str, object]] = []
        for row in raw:
            if not isinstance(row, dict) or set(row) != {"detectorId", "observation"}:
                raise ValueError("public observation row must contain detectorId and observation")
            detector_id = _required_text(row["detectorId"], "detectorId")
            observation = row["observation"]
            _validate_public_observation(observation)
            public.append((detector_id, observation))
        public.sort(key=lambda item: item[0])
        public_ids = [detector_id for detector_id, _ in public]
        if len(public_ids) != len(set(public_ids)):
            raise ValueError("duplicate detectorId in public observations")
        witness_map = witness.observation_map()
        if set(public_ids) != set(witness_map):
            raise ValueError("public observation detector set must match witness detector set")
        for detector_id, observation in public:
            if canonical_json_digest(observation) != witness_map[detector_id].observation_digest:
                raise ValueError(f"public observation digest mismatch for {detector_id}")
        return cls(witness=witness, public_observations=tuple(public))

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "witness": self.witness.to_dict(),
            "publicObservations": [
                {"detectorId": detector_id, "observation": observation}
                for detector_id, observation in self.public_observations
            ],
        }

    def public_observation_map(self) -> dict[str, object]:
        return dict(self.public_observations)


def build_browser_security_witness_bundle(
    *,
    witness_id: str,
    browser_binary_digest: str,
    control_layer: object,
    network_authority: object,
    readings: list[dict[str, object]],
    challenge_standing: str | None = None,
) -> BrowserSecurityWitnessBundle:
    if not isinstance(readings, list) or not readings:
        raise ValueError("at least one browser-security detector reading is required")
    observations: list[DetectorObservation] = []
    public: list[tuple[str, object]] = []
    expected = {"detectorId", "family", "detectorVersion", "coverage", "publicObservation"}
    for row in readings:
        if not isinstance(row, dict) or set(row) != expected:
            raise ValueError("detector reading must contain exactly the canonical fields")
        detector_id = _required_text(row["detectorId"], "detectorId")
        family = _required_text(row["family"], "family")
        if family not in DETECTOR_FAMILIES:
            raise ValueError(f"unsupported browser-security detector family: {family}")
        public_observation = row["publicObservation"]
        _validate_public_observation(public_observation)
        observations.append(
            DetectorObservation(
                detector_id=detector_id,
                family=family,
                detector_version=_required_text(row["detectorVersion"], "detectorVersion"),
                observation_digest=canonical_json_digest(public_observation),
                coverage=_required_text(row["coverage"], "coverage"),
            )
        )
        public.append((detector_id, public_observation))
    observations.sort(key=lambda row: row.detector_id)
    public.sort(key=lambda item: item[0])
    if len({row.detector_id for row in observations}) != len(observations):
        raise ValueError("duplicate detectorId in detector readings")
    witness = BrowserSecurityWitness(
        witness_id=_required_text(witness_id, "witnessId"),
        browser_binary_digest=_digest(browser_binary_digest, "browserBinaryDigest"),
        control_layer_digest=canonical_json_digest(control_layer),
        network_authority_digest=canonical_json_digest(network_authority),
        observations=tuple(observations),
        challenge_standing=(
            None if challenge_standing is None else _required_text(challenge_standing, "challengeStanding")
        ),
        protected_challenge_used_as_detector_oracle=False,
    )
    return BrowserSecurityWitnessBundle(witness=witness, public_observations=tuple(public))


def _changed_json_paths(left: object, right: object, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        changed: list[str] = []
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}.{key}"
            if key not in left or key not in right:
                changed.append(child_path)
            else:
                changed.extend(_changed_json_paths(left[key], right[key], child_path))
        return changed
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        changed: list[str] = []
        for index, (a, b) in enumerate(zip(left, right)):
            changed.extend(_changed_json_paths(a, b, f"{path}[{index}]"))
        return changed
    return [] if left == right else [path]


def compare_browser_security_bundles(
    baseline: BrowserSecurityWitnessBundle, candidate: BrowserSecurityWitnessBundle
) -> dict[str, object]:
    result = compare_browser_security_witnesses(baseline.witness, candidate.witness)
    baseline_public = baseline.public_observation_map()
    candidate_public = candidate.public_observation_map()
    drift_ids = set(result["detectorDrift"])
    changes: list[dict[str, object]] = []
    for row in result["detectors"]:
        detector_id = row["detectorId"]
        if row["status"] != "CHANGED" or detector_id in drift_ids:
            continue
        changes.append(
            {
                "detectorId": detector_id,
                "changedPaths": _changed_json_paths(
                    baseline_public[detector_id], candidate_public[detector_id]
                ),
            }
        )
    result["publicObservationChanges"] = changes
    return result


def compare_browser_security_pool(
    carriers: dict[str, tuple[BrowserSecurityWitnessBundle, BrowserSecurityWitnessBundle]],
) -> dict[str, object]:
    if not isinstance(carriers, dict) or len(carriers) < 2:
        raise ValueError("browser-security pool comparison requires at least two carriers")

    comparisons: dict[str, dict[str, object]] = {}
    family_changes: dict[str, set[str]] = {}
    infrastructure_changes: dict[str, set[str]] = {}
    detector_drift_carriers: list[str] = []
    challenge_change_carriers: list[str] = []

    for carrier_id in sorted(carriers):
        _required_text(carrier_id, "carrierId")
        pair = carriers[carrier_id]
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError(f"carrier {carrier_id} must map to one baseline/candidate bundle tuple")
        baseline, candidate = pair
        if not isinstance(baseline, BrowserSecurityWitnessBundle) or not isinstance(
            candidate, BrowserSecurityWitnessBundle
        ):
            raise ValueError(f"carrier {carrier_id} comparison values must be witness bundles")
        result = compare_browser_security_bundles(baseline, candidate)
        comparisons[carrier_id] = result
        family_changes[carrier_id] = set(result["changedFamilies"])
        infrastructure_changes[carrier_id] = {
            key for key, changed in result["infrastructureChanges"].items() if changed
        }
        detector_shape_drift = any(
            row["status"] in {"ADDED", "MISSING", "DETECTOR_DRIFT"}
            for row in result["detectors"]
        )
        if result["detectorDrift"] or detector_shape_drift:
            detector_drift_carriers.append(carrier_id)
        if result["challengeStandingChanged"]:
            challenge_change_carriers.append(carrier_id)

    carrier_ids = sorted(comparisons)
    if detector_drift_carriers:
        return {
            "schemaVersion": 1,
            "standing": "DETECTOR_DRIFT",
            "carrierIds": carrier_ids,
            "detectorDriftCarriers": detector_drift_carriers,
            "subjectClassificationSuppressed": True,
            "sharedChangedFamilies": [],
            "carrierLocalChangedFamilies": {},
            "sharedInfrastructureChanges": [],
            "carrierLocalInfrastructureChanges": {},
            "challengeStandingChangedCarriers": challenge_change_carriers,
            "perCarrier": comparisons,
            "repairRoutes": [],
            "rootCauseEstablished": False,
        }

    shared_families = set.intersection(*(family_changes[carrier] for carrier in carrier_ids))
    shared_infrastructure = set.intersection(
        *(infrastructure_changes[carrier] for carrier in carrier_ids)
    )
    local_families = {
        carrier: sorted(family_changes[carrier] - shared_families)
        for carrier in carrier_ids
        if family_changes[carrier] - shared_families
    }
    local_infrastructure = {
        carrier: sorted(infrastructure_changes[carrier] - shared_infrastructure)
        for carrier in carrier_ids
        if infrastructure_changes[carrier] - shared_infrastructure
    }
    has_shared = bool(shared_families or shared_infrastructure)
    has_local = bool(local_families or local_infrastructure)
    if not has_shared and not has_local:
        standing = "NO_OBSERVED_DRIFT"
    elif has_shared and has_local:
        standing = "MIXED_DRIFT"
    elif has_shared:
        standing = "GLOBAL_DRIFT"
    else:
        standing = "CARRIER_LOCAL_DRIFT"

    all_changed_families = set(shared_families)
    for families in local_families.values():
        all_changed_families.update(families)

    return {
        "schemaVersion": 1,
        "standing": standing,
        "carrierIds": carrier_ids,
        "detectorDriftCarriers": [],
        "subjectClassificationSuppressed": False,
        "sharedChangedFamilies": sorted(shared_families),
        "carrierLocalChangedFamilies": local_families,
        "sharedInfrastructureChanges": sorted(shared_infrastructure),
        "carrierLocalInfrastructureChanges": local_infrastructure,
        "challengeStandingChangedCarriers": challenge_change_carriers,
        "perCarrier": comparisons,
        "repairRoutes": [REPAIR_ROUTES[family] for family in sorted(all_changed_families)],
        "rootCauseEstablished": False,
    }
