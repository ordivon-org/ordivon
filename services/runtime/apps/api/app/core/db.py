"""
Re-export stub — 旧路径兼容层。

真相源已迁移至: pfios.core.db
此文件仅做 re-export，请在新代码中直接使用:
    from pfios.core.db.session import get_db_connection
    from pfios.core.db.schema import ensure_pipeline_schema
"""
from pfios.core.db.session import get_db_connection, init_db  # noqa: F401
from pfios.core.db.schema import ensure_pipeline_schema  # noqa: F401
