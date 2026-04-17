from fastapi import APIRouter, Depends
from typing import Any, Dict
from pfios.core.db.session import get_db_connection

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """获取仪表盘全局概览数据"""
    conn = get_db_connection(read_only=True)
    try:
        # 1. 建议状态统计
        reco_stats = conn.execute(
            "SELECT lifecycle_status, count(*) FROM recommendations GROUP BY lifecycle_status"
        ).fetchall()
        
        # 2. 最近 5 次结果快照
        recent_outcomes = conn.execute(
            """
            SELECT s.outcome_state, s.trigger_reason, r.symbol, s.observed_at
            FROM outcome_snapshots s
            JOIN recommendations r ON s.recommendation_id = r.recommendation_id
            ORDER BY s.observed_at DESC
            LIMIT 5
            """
        ).fetchall()
        
        # 3. 待处理任务数
        pending_reviews = conn.execute(
            "SELECT count(*) FROM recommendations WHERE lifecycle_status = 'review_pending'"
        ).fetchone()[0]
        
        # 4. 账户状态概览 (示例)
        balance_sum = conn.execute("SELECT sum(total) FROM account_balances").fetchone()[0] or 0
        
        return {
            "recommendation_stats": dict(reco_stats),
            "recent_outcomes": [
                {
                    "state": r[0],
                    "reason": r[1],
                    "symbol": r[2],
                    "timestamp": r[3]
                } for r in recent_outcomes
            ],
            "pending_review_count": pending_reviews,
            "total_balance_estimate": balance_sum,
            "system_health": "nominal"
        }
    finally:
        conn.close()
