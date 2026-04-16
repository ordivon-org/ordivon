import json
from datetime import datetime
from pathlib import Path
from app.core.db import get_db_connection
from app.utils.crypto import make_id

class RecommendationService:
    """建议生命周期服务 (Step 10.2) - 负责建议生成、跟踪与闭环"""
    
    TRACKABLE_ACTIONS = ["accumulate", "reduce", "exit", "hold"]

    @staticmethod
    def auto_generate_if_needed(analysis_result: dict, report_id: str, audit_id: str = None):
        """
        基于分析结果决定是否生成建议对象 (带白名单过滤)
        """
        action = analysis_result.get("action_plan", {}).get("action", "").lower()
        if action not in RecommendationService.TRACKABLE_ACTIONS:
            return None

        # 如果 decision 是 block，通常不建议生成可采纳建议
        if analysis_result.get("decision") == "block":
            return None

        conn = get_db_connection(read_only=False)
        try:
            reco_id = make_id("reco")
            now = datetime.now()
            conn.execute(
                """
                INSERT INTO recommendations (
                    recommendation_id, source_report_id, source_audit_id, symbol,
                    action, confidence, decision, lifecycle_status, review_status,
                    outcome_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reco_id, report_id, audit_id, analysis_result.get("metadata", {}).get("symbol", "UNKNOWN"),
                    action, analysis_result.get("thesis", {}).get("confidence", 0.0),
                    analysis_result.get("decision", "allow"),
                    "generated", "pending", "pending", now
                )
            )
            return reco_id
        finally:
            conn.close()

    @staticmethod
    def update_status(reco_id: str, lifecycle_status: str = None, adopted: bool = None, user_note: str = None):
        """更新建议状态与用户反馈"""
        conn = get_db_connection(read_only=False)
        try:
            updates = []
            params = []
            if lifecycle_status:
                updates.append("lifecycle_status = ?")
                params.append(lifecycle_status)
            if adopted is not None:
                updates.append("adopted = ?, adopted_at = ?")
                params.extend([adopted, datetime.now()])
            if user_note:
                updates.append("user_note = ?")
                params.append(user_note)
            
            if not updates:
                return
            
            params.append(reco_id)
            conn.execute(f"UPDATE recommendations SET {', '.join(updates)} WHERE recommendation_id = ?", params)
        finally:
            conn.close()

    @staticmethod
    def get_recent(limit: int = 10):
        """获取最近建议列表"""
        conn = get_db_connection(read_only=True)
        try:
            result = conn.execute("SELECT * FROM recommendations ORDER BY created_at DESC LIMIT ?", [limit])
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row)) for row in result.fetchall()]
        finally:
            conn.close()
