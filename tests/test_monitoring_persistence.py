import json
from pathlib import Path

from ordivon_capital.market.monitoring_persistence import monitoring_dataframe, persist_monitoring_evidence


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


def test_monitoring_dataframe_uses_pandera_contract():
    df = monitoring_dataframe(_evidence())
    assert list(df["factor"]) == ["F1"]
    assert float(df.iloc[0]["overlap_to_union_ratio"]) == 0.8


def test_persist_monitoring_evidence_parquet_duckdb_mlflow(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(_evidence()))
    result = persist_monitoring_evidence(
        evidence_path=evidence_path,
        output_dir=tmp_path / "out",
        duckdb_binary=DUCKDB,
        tracking_uri=f"sqlite:///{tmp_path / 'mlflow.db'}",
    )
    assert result["rowCount"] == 1
    assert int(result["duckdbReadback"]["row_count"]) == 1
    assert len(result["mlflowRunId"]) == 32
    assert Path(result["parquetPath"]).is_file()
    assert (tmp_path / "mlflow.db").is_file()
    assert result["mlflowTrackingUri"].startswith("sqlite:")
