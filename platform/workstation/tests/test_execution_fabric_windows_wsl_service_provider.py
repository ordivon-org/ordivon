from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PS1=ROOT/"workstation/execution_fabric/providers/windows_wsl_service/WindowsWslServiceControlProvider.ps1"
MAT=ROOT/"workstation/execution_fabric/providers/windows_wsl_service/materialize.py"

def test_service_provider_has_fixed_profiles_and_no_arbitrary_shell():
    text=PS1.read_text()
    lowered=text.lower()
    assert "ordivon-runtime.service" in text
    assert "ordivon-host-v2.service" in text
    assert "ordivon-ef6e-ensure-test.service" in text
    assert "capability/service/probe" in text
    assert "capability/service/ensure" in text
    assert "targetNodeId = 'linux-local'" in text
    for forbidden in ("invoke-expression","cmd.exe","powershell.exe","--terminate","--shutdown"):
        assert forbidden not in lowered

def test_service_provider_converges_not_blind_restart():
    text=PS1.read_text()
    assert "'is-active'" in text
    assert "$inactive.Count -gt 0" in text
    assert "'start'" in text
    assert "restart" not in text.lower()

def test_materializer_declares_linux_target_node():
    text=MAT.read_text()
    assert '"targetNodeIds":["linux-local"]' in text.replace(" ","")
