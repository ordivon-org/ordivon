from pathlib import Path


def test_v2_source_does_not_import_v1() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("src/ordivon_host_v2").rglob("*.py")
    )
    assert "import ordivon_host" not in source
    assert "from ordivon_host" not in source
