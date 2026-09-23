from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ordivon_capital.accounting.durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
    DurableReservationHistory,
    LedgerTransferObservation,
    ReservationStanding,
    binding_for_namespace,
    reconcile_durable_history,
)
from ordivon_capital.accounting.sqlite_ledger import LedgerApplyStatus, SQLiteAccountingLedger
from ordivon_capital.accounting.substrate import (
    AccountingAccount,
    AccountingOperation,
    reservation_instruction,
    resolution_instruction,
    stable_accounting_id,
)
from ordivon_capital.governance.composition_contract import compile_composition
from ordivon_capital.trading.execution_reconciliation import reconcile_fix_intent
from ordivon_capital.trading.simulated_effect import SCENARIOS, simulate_exchange_episode

ROOT = Path(__file__).resolve().parents[3]


class NonLiveEffectCircuitError(ValueError):
    """Fail-closed bounded non-live effect circuit error."""


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text())
    if not isinstance(value, dict):
        raise NonLiveEffectCircuitError(f"expected JSON object: {relative}")
    return value


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def compile_nonlive_effect_circuit(
    *,
    scenario: str,
    intent: Mapping[str, Any],
) -> dict[str, Any]:
    scenario = str(scenario).strip().upper()
    if scenario not in SCENARIOS:
        raise NonLiveEffectCircuitError(f"unsupported non-live scenario: {scenario}")
    admission = _load("contracts/nonlive-effect-admission-v2.json")
    authority = _load("config/nonlive_effect_authority.json")
    production = _load("contracts/production-authorization.json")
    if admission["state"] != "ADMITTED":
        raise NonLiveEffectCircuitError("non-live effect admission is not current")
    if admission["allowedEffectClass"] != "SIMULATED_EXCHANGE_ORDER_EFFECT":
        raise NonLiveEffectCircuitError("unexpected admitted effect class")
    if admission["externalFinancialWriteAllowed"] is not False or admission["realMoney"] is not False:
        raise NonLiveEffectCircuitError("non-live contract widened into financial write")
    if authority["executionMode"] != "BOUNDED_SIMULATED_EXCHANGE" or scenario not in authority["scenarios"]:
        raise NonLiveEffectCircuitError("scenario is not inside current bounded authority")
    if production["state"] != "BLOCK_NOT_GRANTED" or production["externalFinancialWriteAllowed"] is not False:
        raise NonLiveEffectCircuitError("R1 requires production financial writes to remain blocked")

    composition = compile_composition(
        lego_ids=[
            "capital.accounting.sqlite-ledger",
            "capital.trading.simulated-effect",
            "capital.trading.execution-reconciliation",
            "capital.accounting.durable-reconciliation",
        ],
        available_authorities={"LOCAL_STATE", "SIMULATED_EFFECT"},
        requested_use="bounded simulated exchange qualification",
    )
    if composition["effectClasses"] != ["SIMULATED_EXCHANGE_ORDER_EFFECT"]:
        raise NonLiveEffectCircuitError("composition did not bind exactly one simulated effect")

    normalized_intent = dict(intent)
    if normalized_intent.get("protocol") != "FIX.4.4" or normalized_intent.get("msgType") != "D":
        raise NonLiveEffectCircuitError("intent must be FIX 4.4 NewOrderSingle")
    circuit = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.nonlive-effect-circuit",
        "scenario": scenario,
        "intent": normalized_intent,
        "effectClass": "SIMULATED_EXCHANGE_ORDER_EFFECT",
        "stages": ["AUTHORIZE", "RESERVE", "EFFECT", "OBSERVE", "RECONCILE", "ACCOUNT"],
        "compositionStanding": composition["standing"],
        "unresolvedEvidenceObligations": composition["unresolvedEvidenceObligations"],
        "externalFinancialWriteAllowed": False,
        "realMoney": False,
        "productionAuthorization": "BLOCK_NOT_GRANTED",
        "semanticCompletionEvaluated": False,
    }
    circuit["circuitDigest"] = _digest(circuit)
    return circuit


def _checked_circuit(circuit: Mapping[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(dict(circuit), sort_keys=True))
    digest = value.pop("circuitDigest", None)
    if value.get("kind") != "ordivon.capital.nonlive-effect-circuit":
        raise NonLiveEffectCircuitError("unexpected circuit kind")
    if digest != _digest(value):
        raise NonLiveEffectCircuitError("circuit digest mismatch")
    if value.get("externalFinancialWriteAllowed") is not False or value.get("realMoney") is not False:
        raise NonLiveEffectCircuitError("non-live boundary violated")
    value["circuitDigest"] = digest
    return value


def _ledger_observation(instruction) -> LedgerTransferObservation:
    return LedgerTransferObservation(
        transfer_id=instruction.transfer_id,
        operation=instruction.operation,
        amount=instruction.amount,
        pending_id=instruction.pending_id,
    )


def run_nonlive_effect_circuit(
    *,
    circuit: Mapping[str, Any],
    ledger_path: Path,
    reservation_amount: int = 1000,
) -> dict[str, Any]:
    checked = _checked_circuit(circuit)
    if reservation_amount <= 0:
        raise NonLiveEffectCircuitError("reservation_amount must be positive")
    effect_id = checked["circuitDigest"]
    namespace = CapitalAccountNamespace(
        "owner:nonlive-qualification",
        f"parcel:{effect_id}",
    )
    binding = binding_for_namespace(
        namespace=namespace,
        reservation_ref=f"reservation:{effect_id}",
        amount=reservation_amount,
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with SQLiteAccountingLedger(ledger_path) as ledger:
        fund = AccountingAccount(stable_accounting_id("ordivon-capital:nonlive-effect", "fund"))
        for account in (
            fund,
            namespace.account(CapitalAccountRole.AVAILABLE),
            namespace.account(CapitalAccountRole.ENCUMBRANCE),
        ):
            status = ledger.create_account(account)
            if status not in {LedgerApplyStatus.CREATED, LedgerApplyStatus.EXISTS}:
                raise NonLiveEffectCircuitError(f"account creation failed: {status}")
        funding_status = ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("ordivon-capital:nonlive-effect:funding", effect_id),
            debit_account_id=fund.account_id,
            credit_account_id=namespace.available_account_id,
            amount=reservation_amount * 10,
        )
        if funding_status not in {LedgerApplyStatus.CREATED, LedgerApplyStatus.EXISTS}:
            raise NonLiveEffectCircuitError(f"funding failed: {funding_status}")

        pending_instruction = reservation_instruction(binding)
        reservation_status = ledger.apply_instruction(pending_instruction)
        if reservation_status not in {LedgerApplyStatus.CREATED, LedgerApplyStatus.EXISTS}:
            raise NonLiveEffectCircuitError(f"reservation failed: {reservation_status}")

        episode = simulate_exchange_episode(intent=checked["intent"], scenario=checked["scenario"])
        reconciliation = reconcile_fix_intent(
            intent=checked["intent"],
            reality=episode["reality"],
            exact_lookup=episode["exactLookup"],
        )
        disposition = reconciliation["reservationResolution"]
        op = {
            "POST_PENDING_TRANSFER": AccountingOperation.POST_PENDING_TRANSFER,
            "VOID_PENDING_TRANSFER": AccountingOperation.VOID_PENDING_TRANSFER,
            "NO_MUTATION": None,
        }[disposition]
        resolution_ref = None if op is None else f"effect:{effect_id}:{disposition.lower()}"
        resolution = (
            None
            if op is None
            else resolution_instruction(
                binding=binding,
                operation=op,
                resolution_ref=resolution_ref or "",
            )
        )
        resolution_status = None
        if resolution is not None:
            resolution_status = ledger.apply_instruction(resolution)
            if resolution_status not in {LedgerApplyStatus.CREATED, LedgerApplyStatus.EXISTS}:
                raise NonLiveEffectCircuitError(f"resolution failed: {resolution_status}")

        history_standing = {
            "NO_MUTATION": ReservationStanding.RESERVED,
            "VOID_PENDING_TRANSFER": ReservationStanding.RELEASED,
            "POST_PENDING_TRANSFER": ReservationStanding.CONSUMED,
        }[disposition]
        history = DurableReservationHistory(
            binding=binding,
            standing=history_standing,
            resolution_ref=resolution_ref,
        )
        durable = reconcile_durable_history(
            history=history,
            pending=_ledger_observation(pending_instruction),
            resolution=None if resolution is None else _ledger_observation(resolution),
        )
        if durable.standing.value != "MATCH":
            raise NonLiveEffectCircuitError(f"durable reconciliation failed: {durable.standing.value}")

        available = ledger.account(namespace.available_account_id)
        encumbrance = ledger.account(namespace.encumbrance_account_id)

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.nonlive-effect-circuit-result",
        "circuitDigest": checked["circuitDigest"],
        "scenario": checked["scenario"],
        "standing": "MECHANICALLY_COMPLETED_NONLIVE_ONLY",
        "reservationStatus": reservation_status.value,
        "providerEpisode": {
            "providerClass": episode["providerClass"],
            "scenario": episode["scenario"],
            "externalFinancialWritesAttempted": False,
            "realMoney": False,
        },
        "reconciliation": reconciliation,
        "accountingResolution": disposition,
        "resolutionApplyStatus": None if resolution_status is None else resolution_status.value,
        "durableLedgerReconciliation": durable.standing.value,
        "availableAccount": {
            "debitsPending": available.debits_pending,
            "debitsPosted": available.debits_posted,
            "creditsPosted": available.credits_posted,
        },
        "encumbranceAccount": {
            "creditsPending": encumbrance.credits_pending,
            "creditsPosted": encumbrance.credits_posted,
        },
        "externalFinancialWritesAttempted": False,
        "semanticCompletionEvaluated": False,
    }
    result["resultDigest"] = _digest(result)
    return result
