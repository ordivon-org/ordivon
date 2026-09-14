from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import hashlib
from typing import Iterable


NOT_ADMITTED = "NOT_ADMITTED"


class SemanticViolation(ValueError):
    """Fail-closed semantic incompatibility."""


class EffectDisposition(str, Enum):
    RETAIN = "RETAIN"
    RELEASE = "RELEASE"
    CONSUME = "CONSUME"


@dataclass(frozen=True)
class ScientificTruth:
    proof_ref: str


@dataclass(frozen=True)
class EconomicTruth:
    proof_ref: str


@dataclass(frozen=True)
class CapitalTruth:
    proof_ref: str


@dataclass(frozen=True)
class ExternalFinancialWriteAdmission:
    state: str = NOT_ADMITTED

    @property
    def admitted(self) -> bool:
        return self.state == "ADMITTED"


@dataclass(frozen=True)
class ProofObject:
    issuer: str
    subject: str
    resource_identity: str
    generation: str
    source_cut: str
    digest: str
    current: bool
    superseded: bool = False
    revoked: bool = False

    def validate_current(self) -> None:
        if not self.digest.startswith("sha256:") or len(self.digest) != 71:
            raise SemanticViolation("proof digest is not a canonical sha256 identity")
        if self.revoked:
            raise SemanticViolation("revoked proof is terminal without separate ResurrectionAuthority")
        if self.superseded:
            raise SemanticViolation("superseded proof is not current authority")
        if not self.current:
            raise SemanticViolation("proof is not current")


@dataclass(frozen=True)
class WitnessRecord:
    venue: str
    connection_id: str
    raw_bytes: bytes
    recv_monotonic_ns: int
    recv_wall_time: str
    venue_sequence_if_any: str | None
    append_sequence: int
    digest: str
    recorder_instance: str
    recorder_session: str
    clock_domain: str
    config_digest: str
    code_digest: str

    @classmethod
    def build(
        cls,
        *,
        venue: str,
        connection_id: str,
        raw_bytes: bytes,
        recv_monotonic_ns: int,
        recv_wall_time: str,
        venue_sequence_if_any: str | None,
        append_sequence: int,
        recorder_instance: str,
        recorder_session: str,
        clock_domain: str,
        config_digest: str,
        code_digest: str,
    ) -> "WitnessRecord":
        digest = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
        return cls(
            venue=venue,
            connection_id=connection_id,
            raw_bytes=raw_bytes,
            recv_monotonic_ns=recv_monotonic_ns,
            recv_wall_time=recv_wall_time,
            venue_sequence_if_any=venue_sequence_if_any,
            append_sequence=append_sequence,
            digest=digest,
            recorder_instance=recorder_instance,
            recorder_session=recorder_session,
            clock_domain=clock_domain,
            config_digest=config_digest,
            code_digest=code_digest,
        )

    def validate(self) -> None:
        expected = "sha256:" + hashlib.sha256(self.raw_bytes).hexdigest()
        if self.digest != expected:
            raise SemanticViolation("raw bytes digest mismatch")
        if self.recv_monotonic_ns < 0 or self.append_sequence < 0:
            raise SemanticViolation("recorder clock and append sequence must be non-negative")
        for name in ("venue", "connection_id", "recorder_instance", "recorder_session", "clock_domain", "config_digest", "code_digest"):
            if not getattr(self, name):
                raise SemanticViolation(f"missing witness binding: {name}")


def validate_same_cut(records: Iterable[WitnessRecord]) -> tuple[WitnessRecord, ...]:
    rows = tuple(records)
    if not rows:
        raise SemanticViolation("same-cut proof requires at least one witness record")
    for row in rows:
        row.validate()
    instance = rows[0].recorder_instance
    session = rows[0].recorder_session
    clock = rows[0].clock_domain
    last_append = -1
    last_recv = -1
    for row in rows:
        if row.recorder_instance != instance or row.recorder_session != session or row.clock_domain != clock:
            raise SemanticViolation("same-cut requires one recorder instance, session, and clock domain")
        if row.append_sequence <= last_append:
            raise SemanticViolation("append order is not strictly monotone")
        if row.recv_monotonic_ns < last_recv:
            raise SemanticViolation("recorder receive clock regressed")
        last_append = row.append_sequence
        last_recv = row.recv_monotonic_ns
    return rows


def classify_effect_disposition(reconciliation_standing: str) -> EffectDisposition:
    standing = reconciliation_standing.strip().upper()
    if standing in {"UNKNOWN", "AMBIGUOUS", "PARTIAL_OPEN", "CONTRADICTORY"}:
        return EffectDisposition.RETAIN
    if standing in {"PROVEN_NO_EFFECT", "RECONCILED_ZERO_FILL_TERMINAL"}:
        return EffectDisposition.RELEASE
    if standing == "POSITIVE_EXECUTION":
        return EffectDisposition.CONSUME
    raise SemanticViolation(f"unsupported reconciliation standing: {standing}")


def validate_effect_authority_inputs(
    *,
    proof: ProofObject,
    reservation_ref: str,
    effect_admission_ref: str | None,
    policy_allowed: bool,
    write_admission: ExternalFinancialWriteAdmission,
) -> None:
    proof.validate_current()
    if not reservation_ref:
        raise SemanticViolation("reservation identity required")
    if not effect_admission_ref:
        raise SemanticViolation("reservation is not effect admission")
    if reservation_ref == effect_admission_ref:
        raise SemanticViolation("reservation and effect admission require distinct identities")
    if not policy_allowed:
        raise SemanticViolation("generic policy denied")
    if not write_admission.admitted:
        raise SemanticViolation("external financial write admission is not admitted")


_FALSE_GREEN = {
    "ccxt_normalized_event": "normalized market data is not authentic observation evidence",
    "kafka_offset": "stream offset is not cross-venue observation order",
    "nautilus_fill": "engine fill is not real settlement",
    "lean_backtest_profit": "backtest profit is not Economic Truth",
    "tigerbeetle_balance": "ledger balance is not deployable capital",
    "temporal_workflow_success": "workflow completion is not effect success",
    "opa_allow": "generic policy allow is not EffectAuthority",
    "openlineage_graph": "generic lineage is not proof provenance/currentness",
    "fix_ack": "protocol acknowledgement is not economic finality",
    "iso20022_message": "financial message is not legal ownership",
    "tests_pass": "mechanical test success is not external-effect admission",
}


def reject_false_green(claim_kind: str) -> None:
    key = claim_kind.strip().lower()
    if key not in _FALSE_GREEN:
        raise SemanticViolation(f"unknown false-green claim kind: {claim_kind}")
    raise SemanticViolation(_FALSE_GREEN[key])


def witness_field_names() -> set[str]:
    return {f.name for f in fields(WitnessRecord)}
