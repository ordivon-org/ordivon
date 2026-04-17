"""
Re-export stub — 旧路径兼容层。

真相源已迁移至: pfios.core.config.settings
此文件仅做 re-export，请在新代码中直接使用:
    from pfios.core.config.settings import settings, Settings, ROOT_DIR
"""
from pfios.core.config.settings import Settings, settings, ROOT_DIR  # noqa: F401
