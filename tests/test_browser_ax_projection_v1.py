from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "research/experiments/browser_ax_projection_v1.py"
SPEC = importlib.util.spec_from_file_location("browser_ax_projection_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def ax_node(
    node_id: str,
    role: str,
    *,
    name: str = "",
    backend: int | None = None,
    parent: str | None = None,
    children: list[str] | None = None,
    ignored: bool = False,
    properties: dict[str, object] | None = None,
):
    return {
        "nodeId": node_id,
        "backendDOMNodeId": backend,
        "ignored": ignored,
        "role": {"type": "role", "value": role},
        "name": {"type": "computedString", "value": name},
        "parentId": parent,
        "childIds": list(children or []),
        "properties": [
            {"name": key, "value": {"type": "booleanOrUndefined", "value": value}}
            for key, value in (properties or {}).items()
        ],
    }


def test_button_keeps_browser_name_and_nearest_article_context():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node("2", "article", parent="1", children=["3", "4", "5", "6"]),
            ax_node("3", "StaticText", name="COPENHAGEN · DESIGN", parent="2"),
            ax_node("4", "heading", name="The Glasshouse", parent="2"),
            ax_node("5", "StaticText", name="€210 / night", parent="2"),
            ax_node(
                "6",
                "button",
                name="View The Glasshouse",
                backend=80,
                parent="2",
                properties={"focusable": True},
            ),
        ]
    }

    candidates = M.project_ax_candidates(tree)

    assert candidates == [
        {
            "operation": "CLICK",
            "axNodeId": "6",
            "backendDOMNodeId": 80,
            "role": "button",
            "name": "View The Glasshouse",
            "description": None,
            "states": {"focusable": True},
            "context": "COPENHAGEN · DESIGN\nThe Glasshouse\n€210 / night\nView The Glasshouse",
        }
    ]


def test_editable_searchbox_maps_to_fill_and_click_without_recomputing_name():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "searchbox",
                name="Destination",
                backend=3,
                parent="1",
                properties={"focusable": True, "editable": "plaintext", "settable": True},
            ),
        ]
    }

    candidates = M.project_ax_candidates(tree)

    assert [row["operation"] for row in candidates] == ["FILL", "CLICK"]
    assert {row["name"] for row in candidates} == {"Destination"}
    assert all(row["backendDOMNodeId"] == 3 for row in candidates)


def test_combobox_fans_out_only_unselected_ax_options():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "combobox",
                name="Stay category",
                backend=4,
                parent="1",
                children=["3"],
                properties={"focusable": True, "expanded": False},
            ),
            ax_node("3", "generic", parent="2", children=["4", "5", "6"]),
            ax_node("4", "option", name="All stays", parent="3", properties={"selected": True}),
            ax_node("5", "option", name="Design", parent="3", properties={"selected": False}),
            ax_node("6", "option", name="Nature", parent="3", properties={"selected": False}),
        ]
    }

    candidates = M.project_ax_candidates(tree)

    selects = [row for row in candidates if row["operation"] == "SELECT"]
    assert [(row["name"], row["optionName"]) for row in selects] == [
        ("Stay category", "Design"),
        ("Stay category", "Nature"),
    ]
    assert all(row["backendDOMNodeId"] == 4 for row in selects)


@pytest.mark.parametrize(
    ("ignored", "disabled"),
    [(True, False), (False, True)],
)
def test_ignored_or_disabled_action_is_not_projected(ignored: bool, disabled: bool):
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "button",
                name="Danger",
                backend=9,
                parent="1",
                ignored=ignored,
                properties={"focusable": True, "disabled": disabled},
            ),
        ]
    }

    assert M.project_ax_candidates(tree) == []


def test_readonly_textbox_remains_clickable_but_is_not_fillable():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "textbox",
                name="Readonly field",
                backend=14,
                parent="1",
                properties={
                    "focusable": True,
                    "editable": "plaintext",
                    "readonly": True,
                },
            ),
        ]
    }

    candidates = M.project_ax_candidates(tree)

    assert [row["operation"] for row in candidates] == ["CLICK"]


def test_ax_value_is_preserved_for_decision_and_freshness():
    node = ax_node(
        "2",
        "textbox",
        name="Email",
        backend=14,
        parent="1",
        properties={"focusable": True, "editable": "plaintext"},
    )
    node["value"] = {"type": "computedString", "value": "alice@example.com"}
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            node,
        ]
    }

    candidates = M.project_ax_candidates(tree)

    assert [row["value"] for row in candidates] == [
        "alice@example.com",
        "alice@example.com",
    ]


def test_semantic_witness_ignores_ax_node_id_but_binds_semantics_and_identity():
    candidate = {
        "operation": "CLICK",
        "axNodeId": "68",
        "backendDOMNodeId": 80,
        "role": "button",
        "name": "View The Glasshouse",
        "description": None,
        "states": {"focusable": True},
        "context": "COPENHAGEN · DESIGN\nThe Glasshouse\n€210 / night",
    }
    renumbered = {**candidate, "axNodeId": "999"}

    first = M.make_semantic_witness(candidate)
    second = M.make_semantic_witness(renumbered)

    assert first["backendDOMNodeId"] == 80
    assert first["operation"] == "CLICK"
    assert first["optionName"] is None
    assert first["semanticDigest"] == second["semanticDigest"]


def test_semantic_witness_detects_context_change_and_missing_node():
    candidate = {
        "operation": "CLICK",
        "axNodeId": "68",
        "backendDOMNodeId": 80,
        "role": "button",
        "name": "View Casa Flora",
        "description": None,
        "states": {"focusable": True},
        "context": "LISBON · DESIGN\nCasa Flora\n€145 / night",
    }
    witness = M.make_semantic_witness(candidate)

    assert M.check_semantic_witness([candidate], witness)["standing"] == "MATCH"

    changed = {
        **candidate,
        "context": "COPENHAGEN · DESIGN\nCasa Flora\n€145 / night",
    }
    changed_result = M.check_semantic_witness([changed], witness)
    assert changed_result["standing"] == "SEMANTIC_CHANGED"
    assert changed_result["currentSemanticDigest"] != witness["semanticDigest"]

    missing_result = M.check_semantic_witness([], witness)
    assert missing_result["standing"] == "MISSING"


def test_select_witness_binds_option_name_on_shared_backend_node():
    base = {
        "operation": "SELECT",
        "axNodeId": "4",
        "backendDOMNodeId": 4,
        "role": "combobox",
        "name": "Stay category",
        "description": None,
        "states": {"expanded": False},
        "context": "Category\nAll stays\nDesign\nNature",
    }
    design = {**base, "optionName": "Design"}
    nature = {**base, "optionName": "Nature"}
    witness = M.make_semantic_witness(design)

    assert M.check_semantic_witness([nature, design], witness)["standing"] == "MATCH"
    assert M.check_semantic_witness([nature], witness)["standing"] == "MISSING"
