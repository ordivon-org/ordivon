from pathlib import Path


def test_schema_mismatch_diagnostic_tracks_required_schema_version() -> None:
    text = (
        Path(__file__).resolve().parents[1] / "src" / "ordivon_host_v2" / "service.py"
    ).read_text()
    assert "REQUIRED_SCHEMA_VERSION = 9" in text
    assert "required version {REQUIRED_SCHEMA_VERSION}" in text
    assert "required version 5" not in text
