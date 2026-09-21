import fnmatch
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = json.loads((ROOT / "config/external_owner_census.json").read_text())


def test_external_owner_census_has_no_unowned_active_python_module():
    patterns = [
        pattern
        for responsibility in CENSUS["responsibilities"]
        for pattern in responsibility["sourcePatterns"]
    ]
    modules = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/ordivon_capital").rglob("*.py")
        if path.name != "__init__.py"
    ]
    uncovered = [
        module for module in modules
        if not any(fnmatch.fnmatch(module, pattern) for pattern in patterns)
    ]
    assert uncovered == []


def test_old_market_capital_python_namespace_is_retired():
    legacy_path = "src/" + "market" + "_capital"
    tracked = subprocess.run(
        ["git", "ls-files", f"{legacy_path}/**"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tracked == ""
    assert importlib.util.find_spec("market" + "_capital") is None
    for path in [ROOT / "src", ROOT / "tests", ROOT / "scripts", ROOT / "tools"]:
        for file in path.rglob("*"):
            if not file.is_file():
                continue
            try:
                text = file.read_text()
            except UnicodeDecodeError:
                continue
            if file == Path(__file__):
                continue
            legacy_namespace = "market" + "_capital."
            legacy_path = "src/market" + "_capital"
            assert legacy_namespace not in text, file
            assert legacy_path not in text, file


def test_not_instantiated_domains_have_no_local_packages():
    package_names = {path.name for path in (ROOT / "src/ordivon_capital").iterdir() if path.is_dir()}
    for domain in CENSUS["notInstantiatedDomains"]:
        assert domain["standing"] == "NO_LOCAL_DOMAIN_CODE"
        assert domain["domain"] not in package_names


def test_portfolio_surface_is_split_by_real_owner_after_audit():
    by_id = {row["id"]: row for row in CENSUS["responsibilities"]}
    assert by_id["risk-portfolio-observation-and-statistics"]["localStanding"] == "THIN_GLUE_AFTER_OWNER_AUDIT"
    assert by_id["portfolio-counterfactual-projection"]["localStanding"] == "RETAINED_IRREDUCIBLE_READONLY_GLUE"
    assert "OPA for risk-limit decisions" not in by_id["risk-portfolio-observation-and-statistics"]["externalOwners"]
    assert "Current bounded risk-limit decisions are local deterministic rules" in by_id["risk-portfolio-observation-and-statistics"]["localResponsibility"]
    assert "OPA for pre-trade evidence controls" not in by_id["portfolio-counterfactual-projection"]["externalOwners"]
    assert "bounded local deterministic pre-trade policy" in by_id["portfolio-counterfactual-projection"]["localDependencies"]


def test_active_contract_identity_places_market_under_capital():
    roots = [
        ROOT / "src", ROOT / "config", ROOT / "schema", ROOT / "contracts",
        ROOT / "scripts", ROOT / "tools", ROOT / "tests", ROOT / "policy",
    ]
    legacy = "ordivon.market" + "-capital."
    offenders = []
    for root in roots:
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if not file.is_file() or file == Path(__file__):
                continue
            try:
                text = file.read_text()
            except UnicodeDecodeError:
                continue
            if legacy in text:
                offenders.append(file.relative_to(ROOT).as_posix())
    assert offenders == []


def test_every_active_responsibility_has_a_resolved_external_owner_standing():
    unresolved = {"SUBSTITUTION_PRIORITY", "MIGRATION_CANDIDATE", "NO_OWNER_FOUND", "OBSOLETE_CUSTOM"}
    offenders = [row["id"] for row in CENSUS["responsibilities"] if row["localStanding"] in unresolved]
    assert offenders == []

def test_research_data_is_external_owned_not_a_capital_data_platform():
    by_id = {row["id"]: row for row in CENSUS["responsibilities"]}
    row = by_id["research-model-governance"]
    assert row["localStanding"] == "THIN_RESEARCH_BINDING_AFTER_MLFLOW_PANDERA_PANDAS_SUBTRACTION"
    assert "MLflow" in row["externalOwners"]
    assert "OpenLineage for any future actual lineage-event surface" in row["externalOwners"]
    assert "lineage graph" in row["localResponsibility"]
    assert "generic Research/Data platform" in row["localResponsibility"]
    assert "generic Research/Data platform" in row["localResponsibility"]


def test_retained_old_names_are_explicit_external_or_provider_identity_contracts():
    by_id = {row["id"]: row for row in CENSUS["retainedCompatibilityContracts"]}
    assert "prometheus-market-capital-metric-prefix" not in by_id
    retired = {row["id"]: row for row in CENSUS["retiredCompatibilitySurfaces"]}
    assert retired["prometheus-market-capital-observability"]["standing"] == "RETIRED_NO_ACTIVE_CONSUMER"
    assert by_id["tigerbeetle-market-capital-stable-provider-ids"]["standing"] == "HISTORICAL_EVIDENCE_IDENTITY_ONLY"
    assert by_id["wave-a-frozen-target-fixture"]["standing"] == "RETAINED_FROZEN_FIXTURE_IDENTITY"
    assert "historical-physical-repo-source-coordinate" not in by_id
    retired = {row["id"]: row for row in CENSUS["retiredCompatibilitySurfaces"]}
    assert retired["capital-standalone-source-carrier"]["standing"] == "RETIRED_ARCHIVED_SOURCE_COORDINATE"
    assert retired["capital-standalone-source-carrier"]["recovery"]["exactFullTreeRestoreValidated"] is True

def test_portfolio_optimization_and_agent_office_are_candidates_or_references():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    optimizer = owners["portfolio-optimization"]
    assert optimizer["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert "PyPortfolioOpt" in optimizer["owner"]
    assert "DO_NOT_REIMPLEMENT_OPTIMIZERS_IN_ORDIVON" in optimizer["applicability"]

    agent_office = owners["agent-investment-office-reference"]
    assert agent_office["ownerClass"] == "REFERENCE_IMPLEMENTATION"
    assert "NOT_AUTHORITY_OR_EXECUTION_OWNER" in agent_office["applicability"]


def test_reconciliation_retains_local_baseline_until_an_external_candidate_passes_all_gates():
    by_id = {row["id"]: row for row in CENSUS["responsibilities"]}
    row = by_id["trading-execution-reconciliation"]
    assert row["localStanding"] == "RETAIN_BOUNDED_LOCAL_BASELINE_PENDING_EXTERNAL_ADMISSION"
    assert "NautilusTrader reconciliation" in row["candidateMechanics"]
    assert row["providerOwners"] == ["authoritative venue reports"]
    assert row["standardOwners"] == ["FIX lifecycle semantics"]
    assert "do not broaden it into a general OMS/recovery engine" in row["localResponsibility"]


def test_external_existence_is_candidate_evidence_not_automatic_substitution():
    principle = CENSUS['principle']
    assert 'not automatic winners' in principle
    assert 'contract-equivalent comparative qualification' in principle
    assert 'smallest credible local baseline' in principle


def test_comparative_qualification_blocks_premature_external_substitution():
    rows = {row['contractId']: row for row in CENSUS['comparativeQualifications']}
    reconciliation = rows['execution-state-reconciliation']
    assert reconciliation['standing'] == 'NO_CURRENT_EXTERNAL_CANDIDATE_ADMITTED'
    assert reconciliation['codeDeletionAllowed'] is False
    assert reconciliation['externalCandidate']['versions']['2.0.0rc5']['localExecutableQualification'] == 'NOT_COMPLETED_DOWNLOAD_TIMEOUT'

    accounting = rows['capital-reservation-resolution']
    assert accounting['standing'] == 'LOCAL_CROSS_OWNER_SEAM_RETAIN'
    assert accounting['externalCandidate']['semanticSubstitute'] is False


def test_large_external_library_can_lose_to_thin_local_composition():
    rows = {row['contractId']: row for row in CENSUS['comparativeQualifications']}
    es = rows['historical-expected-shortfall']
    assert es['standing'] == 'LOCAL_THIN_COMPOSITION_PREFERRED'
    assert es['localBaseline']['primitiveOwner'] == 'NumPy'
    assert es['externalCandidate']['semanticSubstitute'] == 'BROADER_THAN_CONTRACT'


def test_no_active_contract_means_no_speculative_dependency_adoption():
    rows = {row['contractId']: row for row in CENSUS['comparativeQualifications']}
    for contract_id in (
        'autonomous-portfolio-optimization',
        'broad-research-data-integration',
    ):
        assert rows[contract_id]['standing'] == 'NO_ACTIVE_CONTRACT_NO_ADOPTION'
        assert rows[contract_id]['codeDeletionAllowed'] is False

    qlib = rows['autonomous-quant-rd-workflow']
    assert qlib['standing'] == 'REJECTED_CURRENT_LANGUAGE_BASELINE'
    assert qlib['codeDeletionAllowed'] is False


def test_same_external_project_can_win_one_contract_and_lose_another():
    rows = {row['contractId']: row for row in CENSUS['comparativeQualifications']}
    versions = rows['execution-state-reconciliation']['externalCandidate']['versions']
    assert versions['2.0.0rc4']['effectMatrix'] == 'PASS_NAUTILUS_NONLIVE_EFFECT_RECONCILIATION_MATRIX'
    assert versions['2.0.0rc4']['frozenAtTheOpen'] == 'BLOCKED_UNSUPPORTED_TIF'
    assert versions['1.231.0']['standing'] == 'FAIL_EXACT_RISK_EFFECT_CONTRACT'


def test_latest_stable_language_baseline_is_a_hard_gate():
    baseline = json.loads((ROOT / 'config/language_baseline.json').read_text())
    assert baseline['policy'] == 'LATEST_STABLE_ONLY'
    assert baseline['languages']['python']['requiredVersion'] == '3.14.7'
    assert baseline['languages']['rust']['requiredVersion'] == '1.98.1'
    assert CENSUS['languageAdmissionPolicy']['standing'] == 'HARD_GATE'


def test_historical_qualification_on_old_python_cannot_authorize_adoption():
    rows = {row['contractId']: row for row in CENSUS['comparativeQualifications']}
    recon = rows['execution-state-reconciliation']
    rc4 = recon['externalCandidate']['versions']['2.0.0rc4']
    assert rc4['python'] == '3.12.13'
    assert rc4['languageGate'] == 'FAIL_CURRENT_PYTHON_BASELINE'
    assert rc4['standing'] == 'HISTORICAL_EVIDENCE_ONLY'
    assert recon['standing'] == 'NO_CURRENT_EXTERNAL_CANDIDATE_ADMITTED'
    assert recon['codeDeletionAllowed'] is False


def test_qlib_is_rejected_until_latest_python_is_supported_and_qualified():
    rows = {row['contractId']: row for row in CENSUS['comparativeQualifications']}
    q = rows['autonomous-quant-rd-workflow']
    assert q['standing'] == 'REJECTED_CURRENT_LANGUAGE_BASELINE'
    assert q['languageGate']['pythonRequired'] == '3.14.7'
    assert q['languageGate']['Qlib']['declaredClassifiersThrough'] == '3.12'
    assert q['languageGate']['RD-Agent']['standing'] == 'FAIL'


def test_canonical_language_runners_exist_and_gate_latest_stable():
    python_runner = (ROOT / 'scripts/run-capability-python').read_text()
    rust_runner = (ROOT / 'scripts/run-capability-rust').read_text()
    assert 'check-language-baseline' in python_runner
    assert 'check-language-baseline' in rust_runner
    assert 'rustup run' in rust_runner


def test_candidate_funnel_distinguishes_gate_zero_from_adoption():
    funnel = json.loads((ROOT / "config/external_candidate_funnel.json").read_text())
    rows = {row["project"]: row for row in funnel["candidates"]}
    assert rows["OpenBB"]["languageStanding"] == "PASS_DECLARED"
    assert rows["OpenBB"]["adoptionStanding"] == "NO_ACTIVE_CONTRACT_NO_ADOPTION"
    assert rows["PyPortfolioOpt"]["languageStanding"] == "PASS_DECLARED"
    assert rows["Riskfolio-Lib"]["languageStanding"] == "PASS_BINARY_EVIDENCE"
    assert rows["NautilusTrader"]["adoptionStanding"] == "NO_VERSION_PASSES_ALL_GATES"
    assert rows["Microsoft Qlib"]["languageStanding"] == "FAIL"
    assert rows["Microsoft RD-Agent"]["languageStanding"] == "FAIL"
    assert rows["TradingAgents"]["adoptionStanding"] == "REFERENCE_ONLY_NOT_ADOPTED"
    assert rows["ai-hedge-fund"]["adoptionStanding"] == "REFERENCE_ONLY_NOT_ADOPTED"


def test_unqualified_nautilus_v1_is_not_a_canonical_core_dependency():
    import tomllib

    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "nautilus" not in project.get("dependency-groups", {})
    python_runner = (ROOT / "scripts/run-capability-python").read_text()
    capability_check = (ROOT / "scripts/check-capabilities").read_text()
    assert "--group nautilus" not in python_runner
    assert "--group nautilus" not in capability_check
    assert '"nautilus-trader": "1.231.0"' not in capability_check


def test_current_nautilus_versions_have_no_admitted_winner():
    rows = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    versions = rows["execution-state-reconciliation"]["externalCandidate"]["versions"]
    assert versions["2.0.0rc4"]["standing"] == "HISTORICAL_EVIDENCE_ONLY"
    assert versions["1.231.0"]["languageGate"] == "PASS"
    assert versions["1.231.0"]["effectMatrixObserved"]["DENY"] == "POST_PENDING_TRANSFER"
    assert versions["1.231.0"]["expectedDeny"] == "VOID_PENDING_TRANSFER"
    assert versions["1.231.0"]["standing"] == "FAIL_EXACT_RISK_EFFECT_CONTRACT"
    assert versions["2.0.0rc5"]["standing"] == "CHALLENGER_NOT_ADMITTED"


def test_canonical_docs_do_not_claim_nautilus_is_currently_admitted_owner():
    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text()
    composition = (ROOT / "docs/COMPOSITION_FIRST_2026-09-14.md").read_text()
    assert "NautilusTrader" in architecture
    assert "challenger rather than a canonical core owner" in architecture
    assert "| Trading OMS/Risk mechanics | NautilusTrader candidate |" in composition
    assert "NautilusTrader owns" not in architecture


def test_market_core_source_tree_has_no_nautilus_imports():
    offenders = []
    for file in (ROOT / "src/ordivon_capital").rglob("*.py"):
        text = file.read_text()
        if "nautilus_trader" in text:
            offenders.append(file.name)
    assert offenders == []


def test_policy_owner_was_revoked_after_local_differential_win():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    policy = owners["policy-decision"]
    assert policy["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert policy["owner"] == "Open Policy Agent 1.20.2"

    resp = {row["id"]: row for row in CENSUS["responsibilities"]}
    local = resp["governance-execution-policy"]
    assert local["sourcePatterns"] == ["src/ordivon_capital/governance/policy_decision.py"]
    assert local["localStanding"] == "BOUNDED_LOCAL_DETERMINISTIC_IMPLEMENTATION_PREFERRED"

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    q = quals["bounded-market-policy-decision"]
    assert q["standing"] == "LOCAL_DETERMINISTIC_POLICY_PREFERRED"
    assert q["externalOwnerAdmitted"] is False
    assert q["evidence"]["differentialCases"] == 354
    assert q["evidence"]["differentialMismatches"] == 0


def test_observability_projects_remain_candidates_without_active_market_contract():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    assert owners["observability"]["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert owners["observability"]["owner"] == "Prometheus 3.14.0"
    assert owners["lineage"]["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert owners["telemetry-pipeline"]["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert owners["observability-visualization"]["ownerClass"] == "IMPLEMENTATION_CANDIDATE"


def test_canonical_architecture_does_not_restore_opa_owner_claim():
    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text()
    assert "OPA is the policy decision point" not in architecture
    assert "src/ordivon_capital/governance/opa_policy.py" not in architecture
    assert "bounded local deterministic policy decisions" in architecture


def test_sqlite_owns_current_bounded_accounting_mechanics_not_tigerbeetle():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    assert owners["accounting-mechanics"]["owner"].startswith("SQLite 3.53.1")
    assert owners["accounting-mechanics"]["ownerClass"] == "IMPLEMENTATION_OWNER"
    assert owners["distributed-accounting-candidate"]["owner"] == "TigerBeetle 0.17.9"
    assert owners["distributed-accounting-candidate"]["ownerClass"] == "IMPLEMENTATION_CANDIDATE"

    resp = {row["id"]: row for row in CENSUS["responsibilities"]}
    accounting = resp["capital-accounting-binding"]
    assert accounting["localStanding"] == "THIN_SQLITE_SCHEMA_AND_RESERVATION_BINDING"
    assert any(owner.startswith("SQLite 3.53.1") for owner in accounting["externalOwners"])

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    q = quals["bounded-capital-accounting-substrate"]
    assert q["standing"] == "SQLITE_COMPOSITION_PREFERRED_FOR_CURRENT_BOUNDED_CONTRACT"
    assert q["tigerBeetleOwnerAdmitted"] is False
    assert q["evidence"]["randomizedDifferentialSteps"] == 400
    assert q["evidence"]["randomizedStatusMismatches"] == 0
    assert q["evidence"]["randomizedBalanceMismatches"] == 0


def test_lean_is_explicit_candidate_and_local_sizer_owns_current_exact_contract():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    lean = owners["historical-trading-engine"]
    assert lean["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert lean["owner"] == "QuantConnect LEAN 985ef30"

    resp = {row["id"]: row for row in CENSUS["responsibilities"]}
    sizing = resp["trading-execution-feasibility"]
    assert sizing["localStanding"] == "LOCAL_BOUNDED_US_EQUITY_SIZER_ADMITTED"

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    q = quals["bounded-us-equity-execution-feasibility"]
    assert q["leanOwnerAdmitted"] is False
    assert q["evidence"]["feeAwareLocalDifferential"]["symbolComparisons"] == 57
    assert q["evidence"]["feeAwareLocalDifferential"]["mismatches"] == 0
    assert q["evidence"]["supplyChain"]["standing"] == "BLOCKED_KNOWN_CRITICAL_HIGH_NUGET_ADVISORIES"


def test_stale_market_capital_observability_surface_is_retired_without_live_consumer():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    obs = owners["observability"]
    assert obs["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert obs["owner"] == "Prometheus 3.14.0"
    assert obs["currentStanding"] == "NO_ACTIVE_CAPITAL_OBSERVABILITY_CONTRACT"

    resp = {row["id"]: row for row in CENSUS["responsibilities"]}
    assert "markets-observability-projection" not in resp

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    q = quals["capital-observability-consumer"]
    assert q["standing"] == "RETIRED_NO_ACTIVE_CONSUMER"
    assert q["prometheusOwnerAdmitted"] is False
    assert q["runtimeEvidence"]["networkV2Prometheus"]["marketMetricQuerySeries"] == 0
    assert q["runtimeEvidence"]["nodeExporter"]["active"] is False
    assert q["runtimeEvidence"]["nodeExporter"]["marketTextfilePresent"] is False
    assert q["runtimeEvidence"]["marketRules"]["configured"] == 0
    assert q["runtimeEvidence"]["marketRules"]["activelyLoaded"] is False

def test_responsibility_rows_separate_admitted_mechanics_from_candidates():
    rows = {row["id"]: row for row in CENSUS["responsibilities"]}

    crypto = rows["markets-crypto-runtime"]
    assert any(x.startswith("websockets 17.1") for x in crypto["admittedMechanicsOwners"])
    assert any("NautilusTrader" in x for x in crypto["candidateMechanics"])

    reconciliation = rows["trading-execution-reconciliation"]
    assert "IMPLEMENTATION_OWNER" not in reconciliation["ownerClasses"]
    assert reconciliation["admittedMechanicsOwners"] == []
    assert reconciliation["downstreamSubstrate"].startswith("SQLite")

    portfolio = rows["risk-portfolio-observation-and-statistics"]
    assert any(x.startswith("NumPy 2.5.3") for x in portfolio["admittedMechanicsOwners"])
    assert any("PyPortfolioOpt" in x for x in portfolio["candidateMechanics"])

    counterfactual = rows["portfolio-counterfactual-projection"]
    assert counterfactual["ownerClasses"] == ["ORDIVON_GLUE"]
    assert counterfactual["admittedMechanicsOwners"] == []
    assert "local bounded deterministic policy for pre-trade evidence controls" not in counterfactual["externalOwners"]

    research = rows["research-model-governance"]
    assert any(x.startswith("PyArrow 25.0.1") for x in research["admittedMechanicsOwners"])
    assert any(x.startswith("DuckDB 1.5.5") for x in research["admittedMechanicsOwners"])
    assert any("MLflow 3.16.1" in x for x in research["candidateMechanics"])
    assert any("Pandera 0.33.1" in x for x in research["candidateMechanics"])
    assert any("OpenLineage" in x for x in research["candidateMechanics"])


def test_removed_monitoring_frameworks_cannot_reenter_current_dependency_owner_set():
    rows = {row["id"]: row for row in CENSUS["responsibilities"]}
    research = rows["research-model-governance"]
    admitted = research["admittedMechanicsOwners"]
    assert not any("MLflow" in x for x in admitted)
    assert not any("Pandera" in x for x in admitted)
    assert not any("pandas" in x.lower() for x in admitted)

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    validation = quals["bounded-monitoring-row-validation"]
    assert validation["evidence"]["randomizedDifferentialCases"] == 400
    assert validation["evidence"]["mismatches"] == 0
    assert validation["externalOwnerAdmitted"] is False

    tracking = quals["market-experiment-tracking"]
    assert tracking["standing"] == "NO_ACTIVE_CONTRACT_NO_ADOPTION"

    parquet = quals["typed-parquet-materialization"]
    assert parquet["externalOwnerAdmitted"] is True
    readback = quals["independent-parquet-readback"]
    assert readback["externalOwnerAdmitted"] is True

def test_parquet_and_duckdb_owners_are_requalified_by_exact_cross_engine_contract():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    parquet = owners["parquet-materialization"]
    duckdb = owners["independent-parquet-readback"]
    assert parquet["ownerClass"] == "IMPLEMENTATION_OWNER"
    assert parquet["currentStanding"] == "REQUALIFIED_R16_ADMITTED_FOR_TYPED_COLUMNAR_MATERIALIZATION"
    assert parquet["python3147ExecutableQualification"] == "PASS"
    assert duckdb["ownerClass"] == "IMPLEMENTATION_OWNER"
    assert duckdb["currentStanding"] == "REQUALIFIED_R16_ADMITTED_FOR_INDEPENDENT_PARQUET_READBACK_AND_BOUNDED_ANALYTICAL_ASSERTIONS"

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    materialize = quals["typed-parquet-materialization"]
    readback = quals["independent-parquet-readback"]
    assert materialize["externalOwnerAdmitted"] is True
    assert materialize["evidence"]["producerConsumerRoundTrip"] == "PASS_PYARROW_TO_DUCKDB"
    assert materialize["evidence"]["reverseRoundTrip"] == "PASS_DUCKDB_TO_PYARROW"
    assert materialize["localBaseline"]["sameEnginePyarrowReadbackContractEquivalent"] is False
    assert readback["externalOwnerAdmitted"] is True
    assert readback["evidence"]["independentImplementation"] is True
    assert readback["localBaseline"]["sameEnginePyarrowReadbackContractEquivalent"] is False

def test_websockets_owner_is_requalified_by_independent_raw_wire_contract():
    owners = {row["id"]: row for row in CENSUS["standardsAndOwners"]}
    ws = owners["websocket-client-mechanics"]
    assert ws["ownerClass"] == "IMPLEMENTATION_OWNER"
    assert ws["currentStanding"] == "REQUALIFIED_R17_ADMITTED_FOR_PUBLIC_ASYNC_WEBSOCKET_PROTOCOL_MECHANICS"
    assert ws["python3147ExecutableQualification"] == "PASS"

    quals = {row["contractId"]: row for row in CENSUS["comparativeQualifications"]}
    q = quals["public-async-websocket-protocol-client"]
    assert q["externalOwnerAdmitted"] is True
    assert q["standing"] == "WEBSOCKETS_17_1_REQUALIFIED_R17_RETAIN_AS_NARROW_PROTOCOL_OWNER"
    raw = q["evidence"]["r17RawWireFalsification"]
    assert raw["implementationIndependence"] == "RAW_ASYNCIO_TCP_PEER_NOT_WEBSOCKETS_SERVER"
    assert all(value is True for key, value in raw.items() if key != "implementationIndependence")
    assert q["localBaseline"]["stdlibWebSocketClientAvailable"] is False
