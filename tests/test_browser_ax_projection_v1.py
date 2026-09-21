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


def dom_node(node_name: str, **attributes: str):
    flat: list[str] = []
    for key, value in attributes.items():
        flat.extend([key, value])
    return {"nodeName": node_name, "attributes": flat}


@pytest.mark.parametrize("input_type", ["password", "file", "hidden"])
def test_dom_metadata_blocks_unsafe_input_effects(input_type: str):
    role = "button" if input_type == "file" else "textbox"
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                role,
                name="Sensitive control",
                backend=20,
                parent="1",
                properties={"focusable": True, "editable": "plaintext"},
            ),
        ]
    }

    candidates = M.project_ax_candidates(
        tree,
        dom_metadata={20: dom_node("INPUT", type=input_type)},
    )

    assert candidates == []


def test_contenteditable_generic_is_fillable_from_browser_dom_metadata():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "generic",
                name="Personal statement",
                backend=21,
                parent="1",
                properties={"focusable": True, "editable": "richtext"},
            ),
        ]
    }

    candidates = M.project_ax_candidates(
        tree,
        dom_metadata={21: dom_node("DIV", contenteditable="true")},
    )

    assert [row["operation"] for row in candidates] == ["FILL", "CLICK"]
    assert {row["role"] for row in candidates} == {"generic"}
    assert {row["name"] for row in candidates} == {"Personal statement"}


def test_summary_is_clickable_via_html_affordance_metadata():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "DisclosureTriangle",
                name="Advanced options",
                backend=22,
                parent="1",
                properties={"focusable": True, "expanded": False},
            ),
        ]
    }

    candidates = M.project_ax_candidates(
        tree,
        dom_metadata={22: dom_node("SUMMARY")},
    )

    assert [(row["operation"], row["name"]) for row in candidates] == [
        ("CLICK", "Advanced options")
    ]


def test_gridcell_with_actionable_descendant_is_not_duplicated():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node("2", "row", parent="1", children=["3"]),
            ax_node(
                "3",
                "gridcell",
                name="Open details",
                backend=23,
                parent="2",
                children=["4"],
                properties={"focusable": True},
            ),
            ax_node(
                "4",
                "button",
                name="Open details",
                backend=24,
                parent="3",
                properties={"focusable": True},
            ),
        ]
    }

    candidates = M.project_ax_candidates(tree)

    assert [(row["role"], row["backendDOMNodeId"]) for row in candidates] == [
        ("button", 24)
    ]


def test_frame_identity_is_part_of_candidate_and_witness_identity():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "button",
                name="Apply",
                backend=25,
                parent="1",
                properties={"focusable": True},
            ),
        ]
    }
    candidate = M.project_ax_candidates(tree, frame_id="frame-a")[0]
    witness = M.make_semantic_witness(candidate)

    assert candidate["frameId"] == "frame-a"
    assert witness["frameId"] == "frame-a"
    assert M.check_semantic_witness([candidate], witness)["standing"] == "MATCH"

    wrong_frame = {**candidate, "frameId": "frame-b"}
    assert M.check_semantic_witness([wrong_frame], witness)["standing"] == "MISSING"


def test_outer_accessible_name_whitespace_is_normalized_without_recomputing_name():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "button",
                name="  Apply now  ",
                backend=26,
                parent="1",
                properties={"focusable": True},
            ),
        ]
    }

    assert M.project_ax_candidates(tree)[0]["name"] == "Apply now"


def test_dom_get_document_metadata_flattens_children_shadow_and_iframe_documents():
    document = {
        "root": {
            "nodeName": "#document",
            "backendNodeId": 1,
            "children": [
                {
                    "nodeName": "DIV",
                    "backendNodeId": 2,
                    "shadowRoots": [
                        {
                            "nodeName": "#document-fragment",
                            "backendNodeId": 3,
                            "children": [
                                {"nodeName": "BUTTON", "backendNodeId": 4, "attributes": []}
                            ],
                        }
                    ],
                },
                {
                    "nodeName": "IFRAME",
                    "backendNodeId": 5,
                    "contentDocument": {
                        "nodeName": "#document",
                        "backendNodeId": 6,
                        "children": [
                            {"nodeName": "INPUT", "backendNodeId": 7, "attributes": []}
                        ],
                    },
                },
            ],
        }
    }

    metadata = M.dom_metadata_from_document(document)

    assert set(metadata) == {1, 2, 3, 4, 5, 6, 7}
    assert metadata[4]["nodeName"] == "BUTTON"
    assert metadata[7]["nodeName"] == "INPUT"


def test_strict_dom_metadata_fails_closed_when_candidate_metadata_is_missing():
    tree = {
        "nodes": [
            ax_node("1", "RootWebArea", children=["2"]),
            ax_node(
                "2",
                "button",
                name="Apply",
                backend=100,
                parent="1",
                properties={"focusable": True},
            ),
        ]
    }

    assert M.project_ax_candidates(tree, require_dom_metadata=True) == []

    candidates = M.project_ax_candidates(
        tree,
        dom_metadata={100: dom_node("BUTTON")},
        require_dom_metadata=True,
    )
    assert [(row["operation"], row["name"]) for row in candidates] == [("CLICK", "Apply")]
