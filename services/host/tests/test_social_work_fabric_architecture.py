import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PLAN = ROOT / "planning" / "social-work-fabric-r1.json"


def _plan() -> dict:
    return json.loads(PLAN.read_text())


def test_swf_target_separates_work_social_and_attention() -> None:
    plan = _plan()
    core = plan["targetCore"]
    assert core["workGraph"] == ["ActorRef", "Work", "WorkSnapshot"]
    assert "Space" in core["socialGraph"]
    assert "Topic" in core["socialGraph"]
    assert "Message" in core["socialGraph"]
    assert "Subscription" in core["attentionFabric"]
    assert "Inbox" in core["attentionFabric"]


def test_swf_legacy_shapes_have_no_retention_by_age() -> None:
    plan = _plan()
    dispositions = {row["legacy"]: row["disposition"] for row in plan["swf01CapabilityDisposition"]}
    assert dispositions["Task.as_privileged_collaboration_container"] == "KILL"
    assert dispositions["Board.as_global_core_object"] == "KILL"
    assert "KEEP_FOR_COMPATIBILITY" not in dispositions.values()


def test_swf_migration_is_destructive_not_dual_write() -> None:
    contract = _plan()["swf04KillContract"]
    forbidden = set(contract["forbiddenMigrationStrategies"])
    assert {"DUAL_WRITE", "PERMANENT_ADAPTER", "COMPATIBILITY_FIRST"} <= forbidden
    assert "freeze legacy mutation" in contract["cutoverRule"]
    assert "remove legacy active APIs/schema" in contract["cutoverRule"]


def test_swf_does_not_claim_foreign_authority() -> None:
    owners = _plan()["swf03OwnerBoundary"]
    assert "physical execution" in owners["runtimeOwns"]
    assert "execution admission" in owners["runtimeOwns"]
    assert "authorization" in owners["identitySecurityOwns"]
    assert "effect authority" in _plan()["swf04KillContract"]["forbiddenNewOwners"]
    assert owners["socialFabricOwns"] == [
        "rebuildable CURRENT/ATTENTION/COORDINATION/AUTHORITY projections"
    ]


def test_swf_directed_does_not_claim_private_semantics() -> None:
    principles = set(_plan()["principles"])
    assert "DIRECTED_NE_PRIVATE_WITHOUT_IDENTITY_SECURITY_ENFORCEMENT" in principles


def test_swf_preserves_measured_useful_legacy_legos_only_as_capabilities() -> None:
    dispositions = _plan()["swf01CapabilityDisposition"]
    by_legacy = {row["legacy"]: row for row in dispositions}
    assert by_legacy["Task.revision_expected_revision"]["target"] == "WorkSnapshot optimistic CAS"
    assert by_legacy["Board.client_message_id_idempotency"]["target"] == "Message replay identity"
    assert by_legacy["Board.topic_string"]["target"] == "Topic identity"
    assert (
        by_legacy["attention.delta_global_board_scan"]["target"] == "actor-scoped Attention delta"
    )


def test_actor_kind_can_preserve_unknown_without_identity_inference() -> None:
    model = (ROOT / "src" / "ordivon_host_v2" / "social_work.py").read_text()
    migration = (
        ROOT / "migrations" / "versions" / "0006_social_work_fabric_work_graph.py"
    ).read_text()
    assert 'UNKNOWN = "unknown"' in model
    assert "'unknown','human','agent','service','organization'" in migration


def test_swf99_holds_unproven_optional_legos_off_default_surface() -> None:
    plan = _plan()
    gate = plan["swf99"]
    held = {row["lego"] for row in gate["hold"]}
    assert {"WorkRelation", "CoordinationIntent", "PrivateConfidentialSemantics"} <= held
    assert gate["standing"] == "PASS_PROMOTE_BOUNDED_CORE"
    surface = (ROOT / "src" / "ordivon_host_v2" / "social_work_mcp.py").read_text()
    assert 'name="work.relation.add"' not in surface
    assert 'name="work.relation.list"' not in surface
    assert 'name="intent.declare"' not in surface


def test_swf99_kills_legacy_core_and_control_plane_creep() -> None:
    killed = set(_plan()["swf99"]["kill"])
    assert {
        "TaskPrivilegedCore",
        "BoardFirstClassCore",
        "DualWriteMigration",
        "SocialScheduler",
        "SocialLockLease",
    } <= killed
