"""
Re-export stub — 旧路径兼容层。

真相源已迁移至: shared
"""

from shared.utils.ids import new_id as make_id  # noqa: F401
from shared.time.clock import utc_now as utcnow  # noqa: F401
from shared.utils.jsonx import json_dumps, json_loads  # noqa: F401
from shared.utils.crypto import quantize_down  # noqa: F401
