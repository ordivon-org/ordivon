import re
from pathlib import Path

import pytest


def test_documented_host_schema_is_equal_to_runtime_and_alembic_head() -> None:
    """Bind public documentation to the two actual schema authorities, not stale prose."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from ordivon_host_v2.service import REQUIRED_SCHEMA_VERSION

    root = Path(__file__).parents[1]
    doc = (root / "README.md").read_text(encoding="utf-8")
    stated = re.findall(r"Host v2 runs Social Work Fabric schema (\d+)", doc)
    assert len(stated) == 1, "Host README must declare exactly one active schema version"
    config = Config(str(root / "alembic.ini"))
    assert config.get_main_option("path_separator") == "os"
    migrations = ScriptDirectory.from_config(config)
    head = migrations.get_current_head()
    assert head is not None and head.isdecimal(), "Alembic needs one numeric HEAD"
    assert int(stated[0]) == REQUIRED_SCHEMA_VERSION == int(head)


def test_historical_alembic_migrations_do_not_import_mutable_runtime_schema() -> None:
    root = Path(__file__).parents[1] / "migrations" / "versions"
    for migration in root.glob("*.py"):
        text = migration.read_text()
        assert "from ordivon_host_v2.schema import SCHEMA_SQL" not in text


def test_running_service_does_not_own_schema_ddl() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
    assert "SCHEMA_SQL" not in service
    assert not (root / "schema.py").exists()
    assert "alembic upgrade head" in service


def test_legacy_task_board_runtime_modules_are_physically_retired() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    for name in ("board.py", "attention.py", "checkpoint_contract.py", "models.py"):
        assert not (root / name).exists()
    service = (root / "service.py").read_text()
    for legacy in (
        "def adopt(",
        "def checkpoint(",
        "def resume(",
        "def observe(",
        "list_task_summaries_page",
        "board_messages",
        "task_events",
        "FROM tasks",
        "FROM checkpoints",
    ):
        assert legacy not in service


def test_unclaimed_work_standing_ontology_is_retired_from_active_source() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    text = "\n".join(
        source.read_text() for source in root.glob("*.py") if source.name != "legacy_cutover.py"
    )
    for retired in (
        "workStanding",
        "WorkingCheckpointStanding",
        "WorkingCheckpointWake",
        "executionAdmission",
        "valueNow",
        "blockerKinds",
        "DIRTY_HANDOFF",
    ):
        assert retired not in text


def test_release_python_and_uv_are_owned_by_immutable_mise_pin() -> None:
    root = Path(__file__).parents[1]
    install = (root / "packaging" / "install_release.sh").read_text()
    assert "/usr/bin/python3.14" not in install
    assert ".python-version" in install
    assert '"$RELEASE/mise.toml"' in install
    assert '"$MISE_BIN" which uv' in install
    assert 'install "python@$PYTHON_REQUEST"' in install
    assert '"$MISE_BIN" which python' in install
    assert "ACTUAL_PYTHON" in install
    assert "UV_PYTHON_INSTALL_DIR" in install
    assert "sync --locked" in install
    assert "sync --frozen" not in install
    assert "python find" not in install


def test_python_pin_matches_project_requirement() -> None:
    import tomllib

    root = Path(__file__).parents[1]
    pinned = (root / ".python-version").read_text().strip()
    project = tomllib.loads((root / "pyproject.toml").read_text())
    assert project["project"]["requires-python"] == f"=={pinned}"
    mise = tomllib.loads((root / "mise.toml").read_text())
    assert mise["tools"]["python"] == pinned


def test_host_status_does_not_duplicate_foreign_or_mcp_authorities() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
    for retired in (
        '"interface":',
        '"surfaceVersion":',
        '"toolNames":',
        '"leases": 0',
        '"deployment": {',
        '"continuity": {',
        '"recentActivity":',
        '"terminalTasks":',
    ):
        assert retired not in service


def test_psycopg_owns_jsonb_adaptation_in_active_stores() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    text = "\n".join(
        (root / name).read_text()
        for name in ("work_store.py", "social_store.py", "social_attention.py")
    )
    assert "Jsonb(" in text
    assert "%s::jsonb" not in text


def test_one_shot_legacy_reader_is_not_registered_as_active_mcp_surface() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    mcp = (root / "mcp_server.py").read_text() + (root / "social_work_mcp.py").read_text()
    assert "legacy_cutover" not in mcp
    assert 'name="task.' not in mcp
    assert 'name="board.' not in mcp


def _assert_host_r3_partition(plan: dict) -> None:
    """Host R3 responsibility function, not a new runtime registry or solver."""

    def distinct_nonempty(values: list, label: str) -> None:
        if any(not isinstance(x, str) or not x.strip() for x in values):
            raise ValueError(f"untyped {label}")
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {label}")

    if plan.get("truthRole") != "source-current-owner-map-not-runtime-truth":
        raise ValueError("Host R3 source map is not runtime truth")
    kept = plan["retained"]
    retired = plan["retired"]
    external = plan["externalOwners"]
    distinct_nonempty([x["id"] for x in kept], "retained id")
    # Match the repository's existing canonical LEGO ID grammar: exact ASCII
    # identity, rather than presentation-equivalent Unicode graph vertices.
    if any(re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*", x["id"]) is None for x in kept):
        raise ValueError("noncanonical retained id")
    distinct_nonempty([x["name"] for x in kept], "retained name")
    # Closed Host R3 responsibility classification; do not allow a new
    # unreviewed standing to pretend a retained LEGO has qualified consumers.
    standing_kinds = {
        "IRREDUCIBLE_SEMANTIC_RESIDUE",
        "THIN_DOMAIN_CONTRACT",
        "REPLACEABLE_PROJECTION",
        "EXTERNAL_SUBSTRATE",
        "SMALL_LOCAL_UTILITY",
    }
    if any(
        not isinstance(x.get("standing"), str) or x["standing"] not in standing_kinds for x in kept
    ):
        raise ValueError("untyped retained standing")
    if any(not isinstance(x["owner"], str) or not x["owner"].strip() for x in kept):
        raise ValueError("untyped retained owner")
    distinct_nonempty(retired, "retired name")
    if {x["name"] for x in kept} & set(retired):
        raise ValueError("retained and retired names overlap")
    distinct_nonempty([x["capability"] for x in external], "external capability")
    if any(not isinstance(x["owner"], str) or not x["owner"].strip() for x in external):
        raise ValueError("untyped external owner")


def test_host_r3_partition_is_a_typed_function() -> None:
    """Current R3 is a partitioned responsibility map, NOT retired R2's node graph."""
    import json

    plan = json.loads((Path(__file__).parents[1] / "planning" / "lego-plan-r3.json").read_text())
    _assert_host_r3_partition(plan)


def test_host_r3_rejects_retained_and_retired_collisions() -> None:
    import copy
    import json

    plan = json.loads((Path(__file__).parents[1] / "planning" / "lego-plan-r3.json").read_text())
    duplicate = copy.deepcopy(plan)
    duplicate["retired"].append(duplicate["retained"][0]["name"])
    with pytest.raises(ValueError, match="retained and retired"):
        _assert_host_r3_partition(duplicate)

    duplicate = copy.deepcopy(plan)
    duplicate["retained"].append(copy.deepcopy(duplicate["retained"][0]))
    with pytest.raises(ValueError, match="duplicate retained"):
        _assert_host_r3_partition(duplicate)


@pytest.mark.parametrize(
    "alias", ["K" + chr(0x200D) + "01", chr(0xFF2B) + "01", "K01" + chr(0x200B)]
)
def test_host_r3_rejects_noncanonical_retained_identity(alias: str) -> None:
    """CEGAR: visually equivalent but byte-distinct IDs cannot split one Host LEGO."""
    import copy
    import json

    plan = json.loads((Path(__file__).parents[1] / "planning" / "lego-plan-r3.json").read_text())
    modified = copy.deepcopy(plan)
    modified["retained"].append(
        {**modified["retained"][0], "id": alias, "name": "ShadowContinuityTaskLedger"}
    )
    with pytest.raises(ValueError, match="noncanonical retained id"):
        _assert_host_r3_partition(modified)


@pytest.mark.parametrize("invalid_standing", ["UNVERIFIED", None, True])
def test_host_r3_rejects_unknown_responsibility_standing(invalid_standing: object) -> None:
    """R3 standing is a closed type, not an arbitrary string/Boolean label."""
    import copy
    import json

    plan = json.loads((Path(__file__).parents[1] / "planning" / "lego-plan-r3.json").read_text())
    modified = copy.deepcopy(plan)
    modified["retained"][0]["standing"] = invalid_standing
    with pytest.raises(ValueError, match="untyped retained standing"):
        _assert_host_r3_partition(modified)


def test_host_r3_rejects_duplicate_external_responsibility() -> None:
    import copy
    import json

    plan = json.loads((Path(__file__).parents[1] / "planning" / "lego-plan-r3.json").read_text())
    duplicate = copy.deepcopy(plan)
    duplicate["externalOwners"].append(
        {"capability": duplicate["externalOwners"][0]["capability"], "owner": "Shadow"}
    )
    with pytest.raises(ValueError, match="duplicate external capability"):
        _assert_host_r3_partition(duplicate)


def test_host_lego_r2_unused_projection_retired_r1_and_r3_preserved() -> None:
    """Retire R2 only; R1 now has an actual graph verifier consumer."""
    import json

    planning = Path(__file__).parents[1] / "planning"
    assert not (planning / "lego-plan-r2.json").exists()
    dependencies = json.loads((planning / "lego-plan-r1.json").read_text())
    assert dependencies["truthRole"] == "planning-projection-not-project-truth"
    assert {
        edge["to"]
        for edge in dependencies["edges"]
        if edge["from"] == "O04" and edge["type"] == "DEPENDENCY"
    } == {"O01", "O02"}
    current = json.loads((planning / "lego-plan-r3.json").read_text())
    assert current["schemaVersion"] == 3
    assert current["project"]["id"] == "ordivon-host-v2"
    assert current["truthRole"] == "source-current-owner-map-not-runtime-truth"
    assert current["freezeRule"]["currentDisposition"] == "NO_KERNEL_REOPEN"
    owners = {item["owner"] for item in current["externalOwners"]}
    assert "PostgreSQL" in owners
    assert "Pydantic" in owners


def test_readme_has_one_tool_inventory_owner() -> None:
    """CEGAR regression: an old hard-coded tool count is not a second source of truth."""
    import json

    root = Path(__file__).parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    surface = json.loads((root / "mcp-surface.json").read_text(encoding="utf-8"))
    assert surface["service"] == "ordivon-host-v2"
    assert surface["tools"] and len(surface["tools"]) == len(set(surface["tools"]))
    assert "[`mcp-surface.json`](mcp-surface.json)" in readme
    assert re.search(r"\b\d+\s+MCP tools?\b", readme) is None


def test_readme_current_fabric_contract_does_not_promote_schema_nine_history() -> None:
    """Keep the historical Social Work Fabric R1 document out of current authority."""
    doc = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    assert "`docs/SOCIAL_WORK_FABRIC_R2_SPEC.md`" in doc
    assert "`docs/SOCIAL_WORK_FABRIC_R1.md`" in doc
    assert "current schema-9" not in doc
