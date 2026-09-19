from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"evidence/data-lifecycle/temporal-evolution-r1"

spec=importlib.util.spec_from_file_location("temporal_pilot",ROOT/"scripts/data_temporal_evolution_pilot.py")
mod=importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

def load(name:str):
    return json.loads((BASE/name).read_text())

def test_real_revision_is_representation_only():
    d=load("revision-ledger.json")
    assert d["transition"]["classification"]=="REPRESENTATION_ONLY_REVISION"
    assert d["transition"]["rawBytesEqual"] is False
    assert d["transition"]["schemaEqual"] is True
    assert d["transition"]["logicalRowsEqual"] is True
    assert d["revisions"][0]["encoding"]["strictUtf8Valid"] is False
    assert d["revisions"][1]["encoding"]["strictUtf8Valid"] is True

def test_row_identity_candidate_is_unique():
    d=load("reference-identity-report.json")
    r=d["report"]["rowIdentityCandidate"]
    assert r["duplicateRows"]==0
    assert r["rows"]==r["unique"]

def test_identifier_label_variants_are_not_conflicts():
    d=load("reference-identity-report.json")
    r=d["report"]["research_body_ror_id"]
    assert r["standing"]=="PASS_IDENTIFIER_STABLE"
    assert r["ambiguousLabelsMappingToMultipleIdentifiers"]=={}
    assert "https://ror.org/01zgghk09" in r["identifierLabelVariants"]

def test_schema_evolution_conformance_matrix():
    d=load("schema-evolution-conformance.json")["fixtures"]
    assert d["actual_revision_pair"]["standing"]=="NO_SCHEMA_CHANGE"
    assert d["add_nullable_field"]["standing"]=="ADDITIVE_COMPATIBLE"
    assert d["rename_without_mapping"]["standing"]=="AMBIGUOUS_DROP_ADD"
    assert d["rename_with_explicit_mapping"]["standing"]=="EXPLICIT_RENAME_COMPATIBLE"
    assert d["compatible_type_promotion"]["standing"]=="TYPE_PROMOTION_COMPATIBLE"
    assert d["breaking_type_change"]["standing"]=="BREAKING_TYPE_CHANGE"

def test_processing_order_is_not_source_order():
    d=load("bounded-replay-conformance.json")
    assert d["processingOrderAuthoritative"] is False
    assert d["watermarkApplied"] is False
    assert d["processingOrder"][0]["commit"]==d["sourceRevisionOrder"][1]["commit"]

def test_heavy_components_remain_workload_gated():
    d=load("activation-decision.json")
    assert all(not d[x]["activate"] for x in ["iceberg","debezium","beam","redpandaKafka"])
