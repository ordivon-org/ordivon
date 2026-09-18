from .gate import PresentationGateHooks, presentation_gate
from .inspection import inspect_pptx, verify_openxml_evidence
from .semantics import verify_font_manifest, verify_presentation_semantics

__all__ = [
    "PresentationGateHooks",
    "inspect_pptx",
    "presentation_gate",
    "verify_font_manifest",
    "verify_openxml_evidence",
    "verify_presentation_semantics",
]
