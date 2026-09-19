from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'platform/windows/Ordivon.WindowsJobLauncher.cs'


def test_runtime_launcher_failure_publishes_bounded_attempt_local_error_evidence():
    text = SOURCE.read_text(encoding='utf-8')
    assert 'Options options = null;' in text
    assert 'options != null && options.RuntimeMode' in text
    assert 'TryWriteLauncherErrorEvidence(options, error);' in text
    assert 'const int maxMessageChars = 2048;' in text
    assert 'launcher-error.json' in text
    assert 'WriteTextAtomic(Path.Combine(options.RuntimeBundle, "launcher-error.json"), json);' in text
    for field in ('launchTokenDigest', 'exceptionType', 'message', 'observedUnixMs'):
        assert field in text


def test_launcher_error_evidence_never_replaces_original_failure():
    text = SOURCE.read_text(encoding='utf-8')
    fn = text[text.index('private static void TryWriteLauncherErrorEvidence'):text.index('private static Options ParseOptions')]
    assert 'try' in fn
    assert 'catch' in fn
    assert 'throw;' not in fn
    main = text[text.index('public static int Main'):text.index('private static void TryWriteLauncherErrorEvidence')]
    assert 'Console.Error.WriteLine("ordivon-windows-job-launcher: " + error.Message);' in main
    assert 'return InternalFailureExit;' in main


def test_native_runtime_preserves_launcher_stderr_separately_from_target_output():
    source = (Path(__file__).resolve().parents[1] / "crates/ordivon-runtime-core/src/runtime/windows.rs").read_text(encoding="utf-8")
    native = source[source.index("#[cfg(windows)]\npub(crate) fn spawn_windows_native"):source.index("#[cfg(not(windows))]\npub(crate) fn spawn_windows_native")]
    assert 'spec.bundle_path.join("launcher-stderr.log")' in native
    assert 'fs::File::create(&launcher_stderr_path)' in native
    assert '.stderr(Stdio::from(launcher_stderr))' in native
    assert '.stdout(Stdio::null())' in native
    assert 'Some("windows.launcherStderr")' in native
