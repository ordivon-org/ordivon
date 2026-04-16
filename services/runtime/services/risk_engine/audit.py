from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.db import get_db_connection
from services.risk_engine.models import AuditEvent

class RiskAuditor:
    """风控审计服务 (Audit Layer) - 决策留痕与可信链条"""

    def __init__(self):
        self.log_root = settings.get_abs_path(settings.audit_log_root)
        self.log_root.mkdir(parents=True, exist_ok=True)

    def record_event(self, event: AuditEvent) -> None:
        """
        双轨持久化：DuckDB (查询用) + JSONL (存档与回放用)
        """
        # 1. 结构化日志落盘 (按日分片)
        self._record_to_jsonl(event)
        
        # 2. 数据库落索引 (DuckDB)
        self._record_to_db(event)

    def _record_to_jsonl(self, event: AuditEvent) -> None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_root / f"{date_str}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def _record_to_db(self, event: AuditEvent) -> None:
        conn = get_db_connection()
        try:
            conn.execute("""
                insert into risk_audits (
                    event_id, workflow_name, stage, decision, 
                    subject_id, status, triggered_rules_json,
                    context_summary, details_json, report_path,
                    created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.workflow_name,
                event.stage,
                event.decision.value,
                event.subject_id,
                event.status,
                json.dumps([r.model_dump() for r in event.details.get("triggered_rules", [])]),
                event.context_summary,
                json.dumps(event.details),
                event.report_path,
                event.timestamp
            ))
        finally:
            conn.close()

    def get_recent_audits(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最近的审计记录 (用于 Dashboard 或 Smoke Test)"""
        conn = get_db_connection(read_only=True)
        try:
            res = conn.execute("select * from risk_audits order by created_at desc limit ?", (limit,)).fetchdf()
            return res.to_dict("records")
        finally:
            conn.close()
