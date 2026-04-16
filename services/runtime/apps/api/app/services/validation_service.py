import json
from datetime import datetime, timedelta
from app.core.db import get_db_connection
from app.utils.crypto import make_id

class ValidationService:
    """真实使用验证与稳定化服务 (Step 11.2) - 聚焦当日量化指标与缺陷治理"""

    @staticmethod
    def sync_daily_usage(date_str: str = None):
        """
        聚合现有业务事实，生成/更新日快照记录 (Step 11 核心约束)
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        start_ts = datetime.strptime(date_str, "%Y-%m-%d")
        end_ts = start_ts + timedelta(days=1)
        
        conn = get_db_connection(read_only=False)
        try:
            # 1. 聚合 Analysis Runs (从 signals 表，基于创建时间)
            runs = conn.execute(
                "SELECT count(*) FROM signals WHERE created_at >= ? AND created_at < ?",
                [start_ts, end_ts]
            ).fetchone()[0]

            # 2. 聚合 Recommendations Updated (从 recommendations 表，基于 adopted_at 或创建时间)
            recos = conn.execute(
                "SELECT count(*) FROM recommendations WHERE created_at >= ? AND created_at < ?",
                [start_ts, end_ts]
            ).fetchone()[0]

            # 3. 聚合 Reviews Completed (从 performance_reviews 表)
            reviews = conn.execute(
                "SELECT count(*) FROM performance_reviews WHERE created_at >= ? AND created_at < ?",
                [start_ts, end_ts]
            ).fetchone()[0]

            # 4. 聚合 Blocking Issues (从 risk_audits 统计 block 数)
            blocks = conn.execute(
                "SELECT count(*) FROM risk_audits WHERE decision = 'BLOCK' AND created_at >= ? AND created_at < ?",
                [start_ts, end_ts]
            ).fetchone()[0]

            # 5. 更新或插入 Usage Log (日快照模式)
            conn.execute(
                """
                INSERT OR REPLACE INTO usage_logs (
                    date, analysis_runs, recommendations_updated, 
                    reviews_completed, blocking_issue_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (date_str, runs, recos, reviews, blocks, datetime.now())
            )
            return {"date": date_str, "runs": runs, "recos": recos, "reviews": reviews, "blocks": blocks}
        finally:
            conn.close()

    @staticmethod
    def report_issue(severity: str, area: str, description: str):
        """分级上报缺陷 (Step 11)"""
        conn = get_db_connection(read_only=False)
        try:
            issue_id = make_id("issue")
            conn.execute(
                """
                INSERT INTO issue_triage (
                    issue_id, severity, area, description, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (issue_id, severity, area, description, "open", datetime.now())
            )
            return issue_id
        finally:
            conn.close()

    @staticmethod
    def get_weekly_validation_summary():
        """生成的周汇总报告摘要"""
        conn = get_db_connection(read_only=True)
        try:
            # 获取最近 7 条记录
            logs = conn.execute("SELECT * FROM usage_logs ORDER BY date DESC LIMIT 7").fetchall()
            
            days_used = len(logs)
            analysis_count = sum(l[1] for l in logs) if logs else 0
            open_p0 = conn.execute("SELECT count(*) FROM issue_triage WHERE severity='P0' AND status='open'").fetchone()[0]
            open_p1 = conn.execute("SELECT count(*) FROM issue_triage WHERE severity='P1' AND status='open'").fetchone()[0]
            
            # 判断 go_no_go
            go_no_go = "continue" if open_p0 == 0 and open_p1 < 3 else "stabilize_more"
            
            return {
                "days_used": days_used,
                "analysis_count": analysis_count,
                "open_p0_count": open_p0,
                "open_p1_count": open_p1,
                "go_no_go": go_no_go,
                "key_lessons": ["Ensuring data integrity between workflows is critical."] if go_no_go == "stabilize_more" else []
            }
        finally:
            conn.close()
