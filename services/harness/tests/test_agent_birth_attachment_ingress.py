from __future__ import annotations

import hashlib
import json
from pathlib import Path

from campaign_materialization import CampaignLaunchSpec, RoleCard, compile_request
from conversation_relay_carrier import (
    CarrierAttachment,
    CarrierMaterializationRequest,
    MaterializationStanding,
)
from sqlite_conversation_materializer import (
    SQLiteConversationMaterializer,
    TargetMaterializationObservation,
)
from windows_user_browser_materialization_target import WindowsUserBrowserMaterializationTarget

from ordivon_harness.gateway_execution_port import (
    GatewayCapabilityStanding,
    GatewayExecutionResult,
)
from ordivon_harness.user_browser_gateway import (
    UserBrowserGatewayConfig,
    UserBrowserGatewayController,
)


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def attachment() -> CarrierAttachment:
    return CarrierAttachment(
        staging_relative_path="attachments/paper3-r6.pdf",
        digest="sha256:" + "a" * 64,
        media_type="application/pdf",
        presentation_name="PAPER3_C21_FSE2027_SUBMISSION_R6.pdf",
    )


def test_campaign_attachment_changes_effect_identity_and_binds_request_digest():
    role = RoleCard(agent_id="pc10", role_card="Blind visual reviewer")
    plain = CampaignLaunchSpec(campaign_id="paper3", shared_prompt="Inspect exactly what is attached.", roster=(role,))
    attached = CampaignLaunchSpec(
        campaign_id="paper3",
        shared_prompt="Inspect exactly what is attached.",
        roster=(role,),
        shared_attachments=(attachment(),),
    )
    plain_request = compile_request(plain, role)
    attached_request = compile_request(attached, role)
    assert plain_request.request_id != attached_request.request_id
    assert plain_request.request_digest != attached_request.request_digest
    assert plain_request.attachments == ()
    assert attached_request.attachments == (attachment(),)
    assert attached_request.attachment_digest is not None
    assert f"ATTACHMENT_SET_DIGEST={attached_request.attachment_digest}" in attached_request.bootstrap_prompt


def test_no_attachment_request_keeps_legacy_v2_digest_shape():
    request = CarrierMaterializationRequest(
        request_id="effect-1",
        preparation_digest="sha256:" + "1" * 64,
        bootstrap_prompt="bootstrap",
    )
    import rfc8785

    expected = {
        "schemaVersion": 2,
        "kind": "ordivon.conversation-carrier-materialization-request",
        "requestId": "effect-1",
        "preparationDigest": "sha256:" + "1" * 64,
        "bootstrapPromptDigest": "sha256:" + hashlib.sha256(rfc8785.dumps("bootstrap")).hexdigest(),
    }
    assert request.request_digest == "sha256:" + hashlib.sha256(rfc8785.dumps(expected)).hexdigest()


class RecordingController:
    def __init__(self) -> None:
        self.kwargs = None

    def materialize(self, **kwargs):
        self.kwargs = kwargs
        return {
            "standing": "pre-effect-failed",
            "providerResource": None,
            "evidenceDigest": "sha256:" + "2" * 64,
            "detail": "test hold",
            "providerEffectAttempted": False,
        }

    def reconcile(self, **kwargs):
        return self.materialize(**kwargs)


def test_user_browser_target_verifies_staged_attachment_and_freezes_manifest(tmp_path: Path):
    payload = b"exact-r6-pdf-bytes"
    staged = tmp_path / "attachments" / "paper3-r6.pdf"
    staged.parent.mkdir(parents=True)
    staged.write_bytes(payload)
    item = CarrierAttachment(
        staging_relative_path="attachments/paper3-r6.pdf",
        digest=digest(payload),
        media_type="application/pdf",
        presentation_name="PAPER3_C21_FSE2027_SUBMISSION_R6.pdf",
    )
    request = CarrierMaterializationRequest(
        request_id="effect-attached",
        preparation_digest="sha256:" + "1" * 64,
        bootstrap_prompt="bootstrap",
        attachments=(item,),
    )
    controller = RecordingController()
    target = WindowsUserBrowserMaterializationTarget(state_dir=tmp_path, controller=controller)
    target.materialize(request)
    assert controller.kwargs is not None
    manifest_path = Path(controller.kwargs["attachment_manifest_path"])
    assert manifest_path.is_file()
    assert controller.kwargs["attachment_manifest_digest"] == digest(manifest_path.read_bytes())
    manifest = json.loads(manifest_path.read_text())
    assert manifest["attachmentSetDigest"] == request.attachment_digest
    assert manifest["attachments"] == [item.canonical()]


class FakePort:
    def __init__(self) -> None:
        self.requests = []

    def capability_standing(self, capability):
        return GatewayCapabilityStanding(
            capability=capability,
            configured=True,
            available=True,
            contexts=("limited", "elevated", "active_user"),
            projection_digest="sha256:" + "9" * 64,
        )

    def execute(self, request):
        self.requests.append(request)
        return GatewayExecutionResult(
            operation_ref="ordivon-exec:v1:runtime.windows:job-1",
            native_id="job-1",
            state="succeeded",
            exit_code=0,
            artifact_ids=("attempt-1.stdout",),
            recovery_required=False,
        )

    def read_stdout(self, _result):
        return json.dumps(
            {
                "schemaVersion": 1,
                "kind": "ordivon.windows-user-browser-attempt",
                "effectId": "effect-attached",
                "standing": "pre-effect-failed",
                "providerResource": None,
                "evidenceDigest": "sha256:" + "2" * 64,
                "detail": "test",
                "providerEffectAttempted": False,
            }
        )


def test_gateway_controller_binds_manifest_digest_into_windows_request():
    port = FakePort()
    controller = UserBrowserGatewayController(
        port,
        UserBrowserGatewayConfig(
            workspace_id="ws-user-browser-prod",
            powershell_path=r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            driver_path=r"C:\ProgramData\Ordivon\chat-ingress\windows_user_browser_chatgpt.ps1",
            proxy_url="http://127.0.0.1:19081",
            linux_stage_root="/mnt/c/ProgramData/Ordivon/chat-ingress",
            windows_stage_root=r"C:\ProgramData\Ordivon\chat-ingress",
        ),
    )
    manifest_digest = "sha256:" + "4" * 64
    controller.materialize(
        effect_id="effect-attached",
        request_digest="sha256:" + "1" * 64,
        prompt_path="/mnt/c/ProgramData/Ordivon/chat-ingress/prompts/p.txt",
        prompt_digest="sha256:" + "3" * 64,
        attachment_manifest_path="/mnt/c/ProgramData/Ordivon/chat-ingress/user-browser/attachment-manifests/m.json",
        attachment_manifest_digest=manifest_digest,
    )
    req = port.requests[0]
    assert "-AttachmentManifestPath" in req.args
    assert "-AttachmentManifestDigest" in req.args
    assert req.args[req.args.index("-AttachmentManifestDigest") + 1] == manifest_digest
    assert req.args[req.args.index("-StageRoot") + 1] == r"C:\ProgramData\Ordivon\chat-ingress"
    assert req.request_id == UserBrowserGatewayController._request_id(
        "materialize",
        "effect-attached",
        "sha256:" + "1" * 64,
        "sha256:" + "3" * 64,
        manifest_digest,
    )


def test_windows_driver_marks_attachment_upload_as_effect_boundary():
    text = (
        Path(__file__).resolve().parents[1] / "scripts" / "windows_user_browser_chatgpt.ps1"
    ).read_text()
    assert "AttachmentManifestDigest" in text
    assert "attachment-manifest-digest-mismatch" in text
    assert "attachment-digest-mismatch" in text
    assert "$script:providerEffectAttempted=$true" in text
    assert "attachment upload was not visibly acknowledged by provider UI" in text


def test_campaign_registry_round_trips_digest_bound_attachment(tmp_path: Path):
    from agent_automation_registry import CampaignRegistry

    value = {
        "campaignId": "paper3-pc10-attachment-contract",
        "sharedPrompt": "Inspect only the attached carrier.",
        "roster": [{"agentId": "pc10", "roleCard": "Blind visual reviewer"}],
        "sharedAttachments": [attachment().canonical()],
    }
    registry = CampaignRegistry(tmp_path)
    registered = registry.register(value)
    observed = registry.inspect(registered["campaignRef"])
    assert observed["campaignRef"] == registered["campaignRef"]
    blob = registry.resolve(registered["campaignRef"])
    frozen = json.loads(blob.read_text())
    assert frozen["sharedAttachments"] == [attachment().canonical()]
    assert frozen["campaignId"] == value["campaignId"]


def test_attempt_generation_is_physical_metadata_not_effect_identity():
    first = CarrierMaterializationRequest(
        request_id="effect-generation-stable",
        preparation_digest="sha256:" + "1" * 64,
        bootstrap_prompt="same fixed bootstrap",
        attempt_generation=1,
    )
    second = CarrierMaterializationRequest(
        request_id=first.request_id,
        preparation_digest=first.preparation_digest,
        bootstrap_prompt=first.bootstrap_prompt,
        attempt_generation=2,
    )
    assert first.request_digest == second.request_digest


def test_pre_effect_retry_passes_committed_generation_to_target(tmp_path: Path):
    class PreEffectThenBound:
        def __init__(self):
            self.generations = []

        def materialize(self, request):
            self.generations.append(request.attempt_generation)
            if request.attempt_generation == 1:
                return TargetMaterializationObservation(
                    standing=MaterializationStanding.PRE_EFFECT_FAILED,
                    evidence_digest="sha256:" + "7" * 64,
                    detail="proven before provider effect",
                )
            return TargetMaterializationObservation(
                standing=MaterializationStanding.BOUND,
                provider_conversation_coordinate="https://chatgpt.com/c/retry-bound",
                evidence_digest="sha256:" + "8" * 64,
                detail="bound on explicit pre-effect retry",
            )

        def reconcile(self, request):
            raise AssertionError("reconcile not expected")

        def resume_after_human(self, request):
            raise AssertionError("human resume not expected")

    target = PreEffectThenBound()
    ledger = SQLiteConversationMaterializer(tmp_path / "ledger.sqlite", target)
    request = CarrierMaterializationRequest(
        request_id="effect-retry-generation",
        preparation_digest="sha256:" + "1" * 64,
        bootstrap_prompt="fixed bootstrap",
    )
    first = ledger.materialize(request, now_ms=1)
    second = ledger.materialize(request, now_ms=2)
    assert first.standing is MaterializationStanding.PRE_EFFECT_FAILED
    assert second.standing is MaterializationStanding.BOUND
    assert target.generations == [1, 2]
    assert first.request_digest == second.request_digest == request.request_digest


def test_windows_physical_attempt_identity_changes_only_after_generation_one():
    args = (
        "materialize",
        "effect-attached",
        "sha256:" + "1" * 64,
        "sha256:" + "3" * 64,
        "sha256:" + "4" * 64,
    )
    legacy = UserBrowserGatewayController._request_id(*args)
    generation_one = UserBrowserGatewayController._request_id(*args, attempt_generation=1)
    generation_two = UserBrowserGatewayController._request_id(*args, attempt_generation=2)
    assert generation_one == legacy
    assert generation_two != generation_one
    assert generation_two.startswith("user-browser:materialize:")
