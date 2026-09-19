from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "platform" / "windows" / "Ordivon.WindowsJobLauncher.cs"


def test_launcher_normalizes_runtime_verbatim_paths_before_legacy_path_api():
    text = SRC.read_text(encoding="utf-8")
    assert "NormalizeLauncherPath" in text
    assert 'StartsWith("\\\\\\\\?\\\\UNC\\\\"' in text
    assert 'StartsWith("\\\\\\\\?\\\\"' in text
    assert "options.Executable = NormalizeLauncherPath(options.Executable);" in text
    assert "options.WorkingDirectory = NormalizeLauncherPath(options.WorkingDirectory);" in text
    assert "options.RuntimeBundle = NormalizeLauncherPath(options.RuntimeBundle);" in text
