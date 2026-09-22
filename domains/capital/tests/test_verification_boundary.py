from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_ci_excludes_provider_qualification_surface() -> None:
    mise = (ROOT / "mise.toml").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'python -m pytest -m "not provider_qualification"' in mise
    assert '[tasks."verify:provider"]' in mise
    assert "python -m pytest -m provider_qualification" in mise
    assert "provider_qualification:" in pyproject
