"""Cross-harness Agent Skills catalog primitives.

This package owns discovery/resolution projection only. It does not execute Skill
scripts, install Skills, or grant execution authority.
"""

from .catalog import SkillCatalog, SkillCatalogError, SkillResolution
from .model import EligibilityState, SkillRecord, SkillSource, TrustState

__all__ = [
    "EligibilityState",
    "SkillCatalog",
    "SkillCatalogError",
    "SkillRecord",
    "SkillResolution",
    "SkillSource",
    "TrustState",
]
