from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PS1=ROOT/"workstation/execution_fabric/providers/authority_validation/AuthorityValidationProvider.ps1"
MAT=ROOT/"workstation/execution_fabric/providers/authority_validation/materialize.py"

def test_authority_validator_is_pure_validation():
    text=PS1.read_text()
    lowered=text.lower()
    assert "capability/authority/validate" in text
    assert "mutationAttempted = $false" in text
    assert "issuanceAttempted = $false" in text
    assert "renewalAttempted = $false" in text
    for forbidden in ("--terminate","diskpart","restart-service","start-service","stop-service","new-itemproperty"):
        assert forbidden not in lowered

def test_authority_validator_preserves_r2_binding_fields():
    text=PS1.read_text()
    for field in (
        "restartAuthorized","compactAuthorized","runtimeActiveJobs","hostLeases",
        "runtimeHealth","recoveryRequiredAttempts","distro","vhdPath",
        "gateSha256","controllerSha256","expiresAtUtc"
    ):
        assert field in text

def test_authority_materializer_is_content_addressed():
    text=MAT.read_text().lower()
    assert "sha256" in text
    assert "authorityvalidationprovider" in text
    assert '"issuesauthority":false' in text.replace(" ","")
    assert '"renewsauthority":false' in text.replace(" ","")
