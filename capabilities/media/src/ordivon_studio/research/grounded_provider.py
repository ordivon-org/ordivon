"""Compose the existing R5 tasks into one source-bound provider experiment.

No new inference engine, provider registry or independent evidence authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .grounded_av_tasks import (
    build_crossmodal_tasks,
    build_runtime_timeline_tasks,
    build_speech_tasks,
)
from .grounded_contracts import canonical_digest
from .grounded_text_tasks import build_article_tasks, build_comprehension_tasks


def build_provider_bundle(*, root: Path, replicates: int = 2) -> dict[str, Any]:
    timed_text = json.loads((root / "productions/runtime-introduction/timed-text/narration.en.json").read_text(encoding="utf-8"))
    source_text = (root / "apps/motion-remotion/src/runtime-introduction-master-composition.tsx").read_text(encoding="utf-8")
    tasks = [
        *build_article_tasks(replicates=replicates),
        *build_runtime_timeline_tasks(source_text=source_text, timed_text=timed_text, replicates=replicates),
        *build_speech_tasks(timed_text=timed_text, replicates=replicates),
        *build_crossmodal_tasks(replicates=replicates),
        *build_comprehension_tasks(replicates=replicates),
    ]
    bundle = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-r5-grounded-meaning-provider-bundle",
        "sourceRevisionRole": "caller must bind current Studio revision separately",
        "tasks": tasks,
        "acceptanceLaw": {
            "grounding": "Every semantic observation must cite supplied evidence identifiers; absent evidence must remain absent rather than reconstructed from prior knowledge.",
            "sensitivity": "Known meaning-changing perturbations must change the targeted semantic result.",
            "invariance": "Meaning-preserving paraphrase should preserve the targeted relation/speech result.",
            "counterexample": "Contradiction and omission variants must not be smoothed into the baseline interpretation.",
            "disagreement": "Replicate disagreement is retained as uncertainty evidence rather than hidden by majority vote.",
            "consequence": "Knowledge transfer is measured separately from semantic annotation and is labeled Agent-observer consequence only.",
        },
    }
    bundle["bundleDigest"] = canonical_digest(bundle)
    return bundle
