import json
from copy import deepcopy
from pathlib import Path

import pytest

from ordivon_capital.research.monitoring_persistence import (
    MonitoringPersistenceError,
    monitoring_table,
    persist_monitoring_evidence,
)

DUCKDB = Path("/opt/ordivon/external/duckdb/1.5.5-1/duckdb")


def _evidence():
    return {
        "subject": "dependence-model-monitoring-r1",
        "sourceAuthority": "TEST",
        "baseInstrumentId": "A",
        "holdoutReturnCount": 10,
        "modelMonitoring": {
            "rows": [
                {
                    "factor": "F1",
                    "proxyInstrumentId": "B",
                    "dataQuality": {
                        "overlapObservationCount": 40,
                        "overlapToUnionRatio": "0.800000",
                    },
                    "outcomes": {
                        "primary": {
                            "realizedVarianceReductionVsUnhedged": "0.300000",
                            "realizedMeanAbsoluteError": "0.02000000",
                        }
                    },
                    "drift": {
                        "parameterDrift": {
                            "betaDelta": "0.100000",
                            "correlationDelta": "-0.050000",
                            "residualVarianceRatio": "1.100000",
                        },
                        "distributionDrift": {
                            "baseReturnWassersteinDistance": "0.01000000",
                            "proxyReturnWassersteinDistance": "0.02000000",
                        },
                    },
                }
            ]
        },
    }


def test_monitoring_table_uses_explicit_arrow_contract():
    table = monitoring_table(_evidence())
    assert table.num_rows == 1
    assert table.column("factor").to_pylist() == ["F1"]
    assert table.column("overlap_to_union_ratio").to_pylist() == [0.8]


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (("dataQuality", "overlapObservationCount"), 0, ">= 1"),
        (("dataQuality", "overlapToUnionRatio"), 1.1, "<= 1"),
        (("outcomes", "primary", "realizedMeanAbsoluteError"), -1, ">= 0"),
        (
            ("drift", "distributionDrift", "baseReturnWassersteinDistance"),
            -0.1,
            ">= 0",
        ),
    ],
)
def test_monitoring_validation_fails_closed(path, value, match):
    evidence = deepcopy(_evidence())
    target = evidence["modelMonitoring"]["rows"][0]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(MonitoringPersistenceError, match=match):
        monitoring_table(evidence)


@pytest.mark.provider_qualification
def test_persist_monitoring_evidence_parquet_duckdb_manifest(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(_evidence()))
    result = persist_monitoring_evidence(
        evidence_path=evidence_path,
        output_dir=tmp_path / "out",
        duckdb_binary=DUCKDB,
    )
    assert result["rowCount"] == 1
    assert int(result["duckdbReadback"]["row_count"]) == 1
    assert Path(result["parquetPath"]).is_file()
    assert Path(result["manifestPath"]).is_file()
    assert result["validationImplementation"] == "LOCAL_BOUNDED_ROW_VALIDATION"
    assert result["storageImplementation"] == "PyArrow 25.0.1 / Parquet"
    assert result["independentReadbackImplementation"] == "DuckDB 1.5.5"
    assert result["experimentTrackingClaimed"] is False
    assert result["lineageAuthorityClaimed"] is False
