from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "catalogs/capabilities/packages/multi-agent-work.md"
INDEX = ROOT / "catalogs/capabilities/packages/INDEX.md"
OPERATING = ROOT / "docs/architecture/LONG_RUNNING_MULTI_AGENT_WORK_OPERATING_PROFILE_R1.md"
PROFILE = ROOT / "profiles/oss-contribution/README.md"
GLOSSARY = ROOT / "profiles/oss-contribution/GLOSSARY.md"
LAUNCH_R2 = ROOT / "profiles/oss-contribution/CONTROLLER_LAUNCH_PROMPT_R2.md"
ROLES_R2 = ROOT / "profiles/oss-contribution/ROLE_PROMPTS_R2.md"
PLAN_R2 = ROOT / "docs/superpowers/plans/2026-10-17-oss-contribution-controller-handoff-r2.md"


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
    assert "if the review-escalation policy is triggered, run an independent falsifier" in profile


def test_independent_review_is_exception_driven_not_default_ceremony():
    package = read(PACKAGE)
    operating = read(OPERATING)
    profile = read(PROFILE)
    assert "Independent multi-Agent audit is **exception-driven, not a default ceremony**." in package
    assert "ECC/Matt/Superpowers methods -> owner-native verification" in package
    assert "must not turn every small engineering step into a multi-Agent audit" in operating
    assert "If the primary Agent is highly confident" in operating
    assert "Do **not** assign an independent falsifier/reviewer to every ordinary Issue or patch." in profile
    assert "does not need a second Agent merely for ceremony" in profile


def test_repository_ai_policy_precedes_public_contribution():
    profile = read(PROFILE)
    assert "## Repository AI-contribution admission" in profile
    assert "If such contributions are prohibited" in profile
    assert "If maintainer approval or a human-authored review is required" in profile
    assert "If disclosure is required" in profile
    assert "Do not sign CLA/DCO" in profile


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


def test_r2_controller_recovers_existing_campaign_and_owns_only_routing():
    launch = read(LAUNCH_R2)
    profile = read(PROFILE)
    assert "work:oss:top1000-contribution-campaign-r1:20261017" in launch
    assert "do not spawn a new" in launch.lower()
    assert "You are not the Scout, Reproducer, Patch Agent" in launch
    assert "REVALIDATE" in launch or "revalidate" in launch
    assert "Host Attention/Topic/Work" in launch
    assert "GitHub Actions action_required" in launch
    assert "CLA SUCCESS" in launch
    assert "CHALLENGE_GATED / NOT_ADMISSIBLE" in launch
    assert "not a live Issue or PR database" in launch
    assert "Do not create 1,000 repository Works or thousands of Issue Tasks." in profile


def test_r2_specialist_separation_and_no_mandatory_reviewer():
    roles = read(ROLES_R2)
    launch = read(LAUNCH_R2)
    for role in ("S01", "S02", "R01", "P01", "U01"):
        assert f"## {role}" in roles
        assert role in launch
    assert "## Optional F01" in roles and "F01" in launch
    assert "WRITE SET = 0" in roles
    assert "Do NOT trust a prior local candidate as GREEN" in roles
    assert "not the default for ordinary engineering" in launch
    assert "DO NOT create a standing reviewer" in roles
    assert "one isolated branch/workspace" in roles
    assert "action_required" in roles
    assert "reproducibility and causality only" in roles


def test_r2_handoff_has_real_evidence_and_next_wave_plan():
    launch = read(LAUNCH_R2)
    plan = read(PLAN_R2)
    for ref in ("#4609", "#4611", "#4586", "ws-oss-rtk4586-pnpm-20261017"):
        assert ref in launch
    assert "not a green PR" in plan
    assert "Host snapshot/message" in plan
    assert "Start S01 repo-policy scout" in plan
    assert "new Task, Scheduler, Review Registry or Board service" in plan
