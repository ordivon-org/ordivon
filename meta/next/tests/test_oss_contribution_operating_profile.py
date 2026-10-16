from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "catalogs/capabilities/packages/multi-agent-work.md"
INDEX = ROOT / "catalogs/capabilities/packages/INDEX.md"
OPERATING = ROOT / "docs/architecture/LONG_RUNNING_MULTI_AGENT_WORK_OPERATING_PROFILE_R1.md"
PROFILE = ROOT / "profiles/oss-contribution/README.md"
GLOSSARY = ROOT / "profiles/oss-contribution/GLOSSARY.md"


def read(path: Path) -> str:
    return path.read_text()


def test_multi_agent_work_package_is_indexed_without_becoming_a_subsystem():
    package = read(PACKAGE)
    index = read(INDEX)
    assert "Standing: **READY_FOR_REAL_WORK**" in package
    assert "| Multi-Agent Work Coordination |" in index
    assert "All twelve high-frequency packages" in index
    assert "task-local capability working set" in package
    assert "not an Ordivon subsystem" in package
    assert "No generic Organization Service, Task Service, Board Service" in package


def test_owner_truth_boundaries_remain_separate():
    package = read(PACKAGE)
    operating = read(OPERATING)
    assert "Host continuity != Harness run != Runtime execution != Git/GitHub truth != domain acceptance" in package
    for owner in (
        "Host Work/WorkSnapshot",
        "Harness Agent Automation",
        "Runtime",
        "GitHub/provider",
        "selected mature procedure + Skill",
        "repository/domain/upstream authority",
    ):
        assert owner in operating
    assert "References connect owners; they never transfer truth." in operating


def test_generic_profile_has_small_deep_interface_and_sparse_work_topology():
    operating = read(OPERATING)
    assert "RECOVER -> REVALIDATE -> ROUTE -> EXECUTE -> EVIDENCE -> DISTILL" in operating
    assert "A Wave is not a Work by default." in operating
    assert "one Work per repository merely because it exists" in operating
    assert "one Work per mined Issue" in operating
    assert "a Board/Task mirror of GitHub" in operating
    assert "open/completed/abandoned" in operating


def test_reentry_requires_owner_native_currentness_before_action():
    operating = read(OPERATING)
    required = (
        "attention.reentry(actorRef)",
        "topic.resume(...)",
        "work.get(...)",
        "Runtime exact-reference reconciliation",
        "owner-native revalidation",
        "GitHub Issue/PR/CI/Git state",
    )
    for phrase in required:
        assert phrase in operating
    assert "reasoning/effects only after those checks" in operating


def test_plan_sop_skill_tool_layers_do_not_collapse():
    operating = read(OPERATING)
    assert "**SOP/provider procedure**" in operating
    assert "**Plan/Operating Profile**" in operating
    assert "**Skill**" in operating
    assert "A Plan must not be promoted into an “industry SOP”" in operating
    assert "Tools are below those layers" in operating


def test_oss_profile_uses_profile_stage_markers_not_host_lifecycle_extension():
    profile = read(PROFILE)
    assert "Operating Profile / Plan composition" in profile
    assert "not an industry SOP" in profile
    assert "Stage markers are profile-level semantic labels." in profile
    assert "They do not extend Host's Work lifecycle." in profile
    for stage in (
        "UNIVERSE",
        "REPOSITORY_ADMITTED",
        "ISSUE_ADMITTED",
        "REPRODUCED",
        "ROOT_CAUSED",
        "RED_PROVEN",
        "GREEN",
        "FALSIFIED_OK",
        "OWNER_VERIFIED",
        "PR_READY",
        "PR_OPEN",
        "REVIEW_LOOP",
        "MERGED",
    ):
        assert stage in profile


def test_reproduction_dispositions_are_real_kill_gates():
    profile = read(PROFILE)
    for disposition in (
        "REPRODUCED",
        "FALSE",
        "ALREADY_FIXED",
        "NEEDS_INFO",
        "SECURITY_PRIVATE_ROUTE",
    ):
        assert disposition in profile
    assert "Do not patch a FALSE, ALREADY_FIXED, or NEEDS_INFO case" in profile
    assert "localize root cause before proposing a fix" in profile
    assert "observe RED before changing production behavior" in profile
    assert "run an independent falsifier" in profile


def test_public_write_and_security_authority_stay_external():
    profile = read(PROFILE)
    assert "A local PR_READY result is not permission to publish." in profile
    assert "confirm the action is within the user's effect authority" in profile
    assert "Security-signaled candidates default to repository SECURITY procedure/private disclosure." in profile
    assert "maintainer acceptance/merge decisions" in profile


def test_contribution_case_work_and_ledger_stay_sparse_and_derived():
    profile = read(PROFILE)
    assert "Do not create 1,000 repository Works or thousands of Issue Tasks." in profile
    assert "A mined Issue stays a dataset row until there is active durable work." in profile
    assert "Do not create a second authoritative ledger database by default." in profile
    assert "derived/reporting view" in profile


def test_glossary_freezes_campaign_language_without_implementation_details():
    glossary = read(GLOSSARY)
    for term in (
        "**Campaign**",
        "**Wave**",
        "**Contribution Case**",
        "**Repository Admission**",
        "**Issue Admission**",
        "**Stage Marker**",
        "**Reproduction Disposition**",
        "**Independent Falsifier**",
        "**Owner-native Verification**",
        "**Contribution Contract**",
        "**Contribution Ledger**",
        "**Handoff**",
        "**Evidence Reference**",
    ):
        assert term in glossary
    assert "not a Host Work lifecycle state" in glossary
    assert "not a second authoritative task or GitHub database" in glossary
