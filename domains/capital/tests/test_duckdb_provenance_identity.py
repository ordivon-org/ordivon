from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_duckdb_launcher_engine_and_package_identities_are_distinct_and_exact():
    deps = json.loads((ROOT / "config/capability_dependencies.json").read_text())
    research = deps["capabilities"]["research"]

    assert research["duckdbLauncherSha256"] == (
        "9268d6c7b8853d3b78a38c806da4b6c3905bbdb76d76429ca0994af3eae4b2d0"
    )
    assert research["duckdbEngineSha256"] == (
        "02f1b93ff8b0dc40f3600b04d55b5f2ca4e968ef22e8c1a3cc49dcf34f880a06"
    )
    assert research["duckdbLauncherSha256"] != research["duckdbEngineSha256"]
    assert research["duckdbPackageSha256"] == (
        "81a5ec42e26876ba0161fde1a29b6b7bf822ccbbc08bb063a05842016a728136"
    )
    assert research["duckdbPackageSignatureVerification"].startswith("PASS_")

    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    quals = {row["contractId"]: row for row in census["comparativeQualifications"]}
    for key in ("typed-parquet-materialization", "independent-parquet-readback"):
        evidence = quals[key]["evidence"]
        assert "duckdbBinarySha256" not in evidence
        assert evidence["duckdbLauncherSha256"] == research["duckdbLauncherSha256"]
        assert evidence["duckdbEngineSha256"] == research["duckdbEngineSha256"]
        assert evidence["provenanceCorrection"] == "R19_LAUNCHER_ENGINE_IDENTITY_SPLIT"
        assert evidence["parquetRequiredOptionalFidelity"] is True
        assert evidence["multiRowGroups"] == 9
