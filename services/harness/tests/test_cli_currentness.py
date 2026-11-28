"""Consumer-facing Harness CLI grammar and current operational guide contract.

The spec's first negative test: obsolete SQLite-era commands must not be
advertised, and canonical operator examples must be parseable with the
installed CLI grammar. No PostgreSQL service or Provider credential required.
"""

from __future__ import annotations

import argparse
import contextlib
import io
from pathlib import Path
import re
import shlex
import unittest

from ordivon_harness.cli import build_parser


ROOT = Path(__file__).resolve().parents[1]
CURRENT_GUIDES = (
    "README.md",
    "docs/QUICKSTART.md",
    "docs/OPERATIONS.md",
    "docs/STATUS.md",
)
REMOVED = {"store-backup", "store-verify-backup", "store-restore"}


def cli_guide_invocations(text: str):
    """Yield complete shell-example commands only, not inline historical prose."""
    for code in re.findall(r"```(?:bash|sh)\n(.*?)\n```", text, flags=re.S):
        lines = code.splitlines()
        for index, raw in enumerate(lines):
            stripped = raw.strip()
            if not stripped.startswith("ordivon-harness "):
                continue
            while stripped.endswith("\\") and index + 1 < len(lines):
                index += 1
                stripped = stripped[:-1] + " " + lines[index].strip()
            yield stripped


class CurrentCliContract(unittest.TestCase):
    def test_parser_exposes_no_retired_commands_or_flags(self):
        parser = build_parser()
        help_text = parser.format_help()
        self.assertNotIn("--state-root", help_text)
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                self.assertFalse(REMOVED.intersection(action.choices))

    def test_wheel_gate_tracks_exact_current_cli_commands(self):
        # The isolated wheel smoke contract must neither demand retired verbs
        # nor omit valid ones. This catches drift missed by package unit tests.
        from check_wheel import CLI_COMMANDS

        parser = build_parser()
        command_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        self.assertEqual(len(command_actions), 1)
        self.assertEqual(set(CLI_COMMANDS), set(command_actions[0].choices))

    def test_live_guides_describe_parseable_commands(self):
        parser = build_parser()
        checked = 0
        for relative_path in CURRENT_GUIDES:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            for command in cli_guide_invocations(text):
                with self.subTest(path=relative_path, command=command):
                    arguments = shlex.split(command)[1:]
                    with contextlib.redirect_stderr(io.StringIO()):
                        try:
                            parser.parse_args(arguments)
                        except SystemExit as exc:
                            self.fail(f"current guide CLI cannot be parsed ({exc.code}): {command}")
                    checked += 1
        self.assertGreater(checked, 12, "no meaningful operator examples scanned")

    def test_document_checker_rejects_a_regressed_cli_example(self):
        # Negative control: a syntactically valid shell command is not
        # necessarily a real supported Harness CLI command.
        from check_docs import validate_live_cli_examples

        bogus = {"docs/QUICKSTART.md": "```bash\nordivon-harness capabilities\n```"}
        errors = validate_live_cli_examples(bogus)
        self.assertTrue(errors)
        self.assertIn("capabilities", "\n".join(errors))

    def test_current_status_reports_pg_as_cli_authority_not_sqlite_writer(self):
        status = (ROOT / "docs/STATUS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("SQLite Journal/CAS is the current Run writer", status)
        self.assertNotIn("only current writer is the Harness SQLite", readme)
        self.assertIn("PostgreSQL", status)
        self.assertIn("PostgreSQL", readme)


if __name__ == "__main__":
    unittest.main()
