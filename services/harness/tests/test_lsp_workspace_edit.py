from __future__ import annotations

import unittest

from ordivon_harness.adaptive_edit import EditCompileError, SourceSnapshot
from ordivon_harness.lsp_workspace_edit import (
    LspDocumentBinding,
    workspace_edit_to_canonical_plan,
)

DIGEST = "sha256:" + "1" * 64


def binding(
    uri: str = "file:///workspace/demo.py",
    *,
    content: str = "alpha = 1\nbeta = 2\n",
    path: str = "demo.py",
    version: int | None = 7,
) -> LspDocumentBinding:
    return LspDocumentBinding(uri, SourceSnapshot(path, DIGEST, content), version)


class LspWorkspaceEditTests(unittest.TestCase):
    def test_changes_compile_multiple_text_edits_into_one_canonical_file_patch(self) -> None:
        plan = workspace_edit_to_canonical_plan(
            {
                "changes": {
                    "file:///workspace/demo.py": [
                        {
                            "range": {
                                "start": {"line": 0, "character": 8},
                                "end": {"line": 0, "character": 9},
                            },
                            "newText": "10",
                        },
                        {
                            "range": {
                                "start": {"line": 1, "character": 7},
                                "end": {"line": 1, "character": 8},
                            },
                            "newText": "20",
                        },
                    ]
                }
            },
            bindings=(binding(),),
            position_encoding="utf-16",
        )
        self.assertEqual(plan.codec, "lsp-workspace-edit-v1")
        self.assertEqual(len(plan.files), 1)
        self.assertEqual(len(plan.files[0].edits), 2)
        self.assertEqual([edit.expected_text for edit in plan.files[0].edits], ["1", "2"])
        self.assertEqual(plan.files[0].expected_digest, DIGEST)

    def test_versioned_document_edit_requires_exact_bound_version(self) -> None:
        edit = {
            "documentChanges": [
                {
                    "textDocument": {"uri": "file:///workspace/demo.py", "version": 6},
                    "edits": [
                        {
                            "range": {
                                "start": {"line": 0, "character": 8},
                                "end": {"line": 0, "character": 9},
                            },
                            "newText": "3",
                        }
                    ],
                }
            ]
        }
        with self.assertRaisesRegex(EditCompileError, "version differs"):
            workspace_edit_to_canonical_plan(
                edit, bindings=(binding(version=7),), position_encoding="utf-16"
            )
        with self.assertRaisesRegex(EditCompileError, "no caller-owned document version"):
            workspace_edit_to_canonical_plan(
                edit, bindings=(binding(version=None),), position_encoding="utf-16"
            )

    def test_null_document_version_still_binds_exact_source_digest(self) -> None:
        plan = workspace_edit_to_canonical_plan(
            {
                "documentChanges": [
                    {
                        "textDocument": {
                            "uri": "file:///workspace/demo.py",
                            "version": None,
                        },
                        "edits": [
                            {
                                "range": {
                                    "start": {"line": 0, "character": 8},
                                    "end": {"line": 0, "character": 9},
                                },
                                "newText": "3",
                            }
                        ],
                    }
                ]
            },
            bindings=(binding(),),
            position_encoding="utf-16",
        )
        self.assertEqual(plan.files[0].expected_digest, DIGEST)

    def test_utf16_surrogate_offset_converts_to_unicode_runtime_column(self) -> None:
        content = 'prefix = "😀x"\n'
        plan = workspace_edit_to_canonical_plan(
            {
                "changes": {
                    "file:///workspace/demo.py": [
                        {
                            "range": {
                                "start": {"line": 0, "character": 12},
                                "end": {"line": 0, "character": 13},
                            },
                            "newText": "y",
                        }
                    ]
                }
            },
            bindings=(binding(content=content),),
            position_encoding="utf-16",
        )
        edit = plan.files[0].edits[0]
        self.assertEqual(edit.expected_text, "x")
        self.assertEqual((edit.start_column, edit.end_column), (11, 12))

    def test_utf16_offset_cannot_split_surrogate_pair(self) -> None:
        with self.assertRaisesRegex(EditCompileError, "splits an encoded character"):
            workspace_edit_to_canonical_plan(
                {
                    "changes": {
                        "file:///workspace/demo.py": [
                            {
                                "range": {
                                    "start": {"line": 0, "character": 11},
                                    "end": {"line": 0, "character": 12},
                                },
                                "newText": "z",
                            }
                        ]
                    }
                },
                bindings=(binding(content='prefix = "😀x"\n'),),
                position_encoding="utf-16",
            )

    def test_unbound_uri_and_resource_operation_fail_closed(self) -> None:
        with self.assertRaisesRegex(EditCompileError, "not bound to Harness authority"):
            workspace_edit_to_canonical_plan(
                {
                    "changes": {
                        "file:///outside/demo.py": [
                            {
                                "range": {
                                    "start": {"line": 0, "character": 0},
                                    "end": {"line": 0, "character": 1},
                                },
                                "newText": "x",
                            }
                        ]
                    }
                },
                bindings=(binding(),),
                position_encoding="utf-16",
            )
        with self.assertRaisesRegex(EditCompileError, "resource operations"):
            workspace_edit_to_canonical_plan(
                {
                    "documentChanges": [
                        {
                            "kind": "create",
                            "uri": "file:///workspace/new.py",
                        }
                    ]
                },
                bindings=(binding(),),
                position_encoding="utf-16",
            )

    def test_duplicate_uri_aliases_are_deduplicated_only_when_identical(self) -> None:
        edits = [
            {
                "range": {
                    "start": {"line": 0, "character": 8},
                    "end": {"line": 0, "character": 9},
                },
                "newText": "3",
            }
        ]
        b1 = binding("file:///workspace/demo.py")
        b2 = binding("file:///alias/demo.py")
        plan = workspace_edit_to_canonical_plan(
            {"changes": {b1.uri: edits, b2.uri: edits}},
            bindings=(b1, b2),
            position_encoding="utf-16",
        )
        self.assertEqual(len(plan.files), 1)
        self.assertEqual(len(plan.files[0].edits), 1)

        conflicting = [
            {
                "range": {
                    "start": {"line": 0, "character": 8},
                    "end": {"line": 0, "character": 9},
                },
                "newText": "4",
            }
        ]
        with self.assertRaisesRegex(EditCompileError, "conflicting edit sets"):
            workspace_edit_to_canonical_plan(
                {"changes": {b1.uri: edits, b2.uri: conflicting}},
                bindings=(b1, b2),
                position_encoding="utf-16",
            )

    def test_overlapping_text_edits_fail_closed(self) -> None:
        with self.assertRaisesRegex(EditCompileError, "overlap"):
            workspace_edit_to_canonical_plan(
                {
                    "changes": {
                        "file:///workspace/demo.py": [
                            {
                                "range": {
                                    "start": {"line": 0, "character": 0},
                                    "end": {"line": 0, "character": 5},
                                },
                                "newText": "a",
                            },
                            {
                                "range": {
                                    "start": {"line": 0, "character": 4},
                                    "end": {"line": 0, "character": 8},
                                },
                                "newText": "b",
                            },
                        ]
                    }
                },
                bindings=(binding(),),
                position_encoding="utf-16",
            )

    def test_unsupported_position_encoding_fails_closed(self) -> None:
        with self.assertRaisesRegex(EditCompileError, "unsupported LSP position encoding"):
            workspace_edit_to_canonical_plan(
                {"changes": {}},
                bindings=(binding(),),
                position_encoding="utf-7",
            )


if __name__ == "__main__":
    unittest.main()
