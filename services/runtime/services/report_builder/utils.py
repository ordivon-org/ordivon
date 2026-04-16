from __future__ import annotations
import re
from datetime import datetime

def slugify(text: str) -> str:
    """生成 URL/文件友好的 Slug"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text

def format_timestamp(ts: str | datetime | None = None) -> str:
    """统一时间格式化"""
    if not ts:
        dt = datetime.now()
    elif isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            dt = datetime.now()
    else:
        dt = ts
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def list_to_md(items: list[str]) -> str:
    """将列表转换为 Markdown 无序列表"""
    if not items:
        return "*N/A*"
    return "\n".join([f"- {i}" for i in items])
