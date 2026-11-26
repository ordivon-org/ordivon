"""Independent stage sequence and Markdown-context metamorphic checks."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordivon_studio.cognition_sections import extract_learning
from ordivon_studio.production_validation import _validate_cognition_record

STAGES = ("FRAME", "BIND", "EXPRESS", "RENDER", "AUDIT", "DECIDE", "LEARNING")


def document(stages):
    return "\n\n".join(f"## {stage}\n\nbody-{stage}" for stage in stages)


class CognitionStructureTests(unittest.TestCase):
    def test_protocol_exact_unique_order(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cognition.md"
            base = document(STAGES)
            path.write_text(base)
            self.assertEqual(_validate_cognition_record(path), [])
            self.assertEqual(extract_learning(base), "body-LEARNING")
            for i in range(len(STAGES)):
                with self.subTest(missing=i):
                    path.write_text(document(STAGES[:i] + STAGES[i+1:]))
                    self.assertTrue(any("missing cognition section" in e for e in _validate_cognition_record(path)))
                with self.subTest(duplicate=i):
                    path.write_text(document(STAGES + (STAGES[i],)))
                    self.assertTrue(any("duplicate cognition section" in e for e in _validate_cognition_record(path)))
            for i in range(len(STAGES)-1):
                with self.subTest(adjacent_swap=i):
                    stages = list(STAGES)
                    stages[i], stages[i+1] = stages[i+1], stages[i]
                    path.write_text(document(stages))
                    self.assertTrue(any("out of protocol order" in e for e in _validate_cognition_record(path)))

    def test_markdown_structure_not_text_substrings(self):
        base = document(STAGES)
        decoys = (
            "```md\n" + base + "\n```\n",
            "\n".join("> " + line for line in base.splitlines()),
            "\n".join("    " + line for line in base.splitlines()),
            base.replace("## FRAME", "## FRAMEWORK").replace("## LEARNING", "## LEARNINGFUL"),
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cognition.md"
            for decoy in decoys:
                with self.subTest(decoy=decoy[:25]):
                    path.write_text(decoy)
                    self.assertTrue(_validate_cognition_record(path))
                    self.assertIsNone(extract_learning(decoy))
            # A code example and quote containing fake protocol stages do not
            # perturb the genuine sequence or cause duplicate admission.
            decorated = decoys[0] + "\n\n" + decoys[1] + "\n\n" + base
            path.write_text(decorated)
            self.assertEqual(_validate_cognition_record(path), [])
            self.assertEqual(extract_learning(decorated), "body-LEARNING")

    def test_learning_excerpt_preserves_native_nested_structure(self):
        source = ("# Title\n\n## LEARNING ##\n\nretained\n\n"
                  "```md\n## FAKE\n```\n\n> ## QUOTE\n\n"
                  "### Scope\n\nlocal only\n\n## Other\n\nnot retained")
        self.assertEqual(extract_learning(source),
                         "retained\n\n```md\n## FAKE\n```\n\n> ## QUOTE\n\n### Scope\n\nlocal only")
        self.assertIsNone(extract_learning("## LEARNING\n\na\n\n## LEARNING\n\nb"))
