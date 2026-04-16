import yaml
from datetime import datetime
from pathlib import Path
from app.core.db import get_db_connection
from app.core.config import settings
from app.utils.crypto import make_id
from app.services.object_service import ObjectService

class ReviewService:
    """复盘与知识沉淀服务 (Step 10.4) - 负责事后对比与经验存档"""

    @staticmethod
    def generate_review_skeleton(report_id: str, reco_id: str = None):
        """基于报告和建议自动生成复盘骨架 (Skeleton)"""
        conn = get_db_connection(read_only=True)
        try:
            # 简化查询: 这里假设 report 已经存在于审计或报告库中
            # 为了第一版演示，我们从 recommendations 表拉取元数据
            reco = None
            if reco_id:
                res = conn.execute("SELECT * FROM recommendations WHERE recommendation_id = ?", [reco_id]).fetchone()
                if res:
                    cols = [d[0] for d in conn.execute("SELECT * FROM recommendations LIMIT 0").description]
                    reco = dict(zip(cols, res))
            
            skeleton = {
                "review_id": make_id("rev"),
                "linked_report_id": report_id,
                "linked_recommendation_id": reco_id,
                "symbol": reco.get("symbol") if reco else "UNKNOWN",
                "expected_outcome": f"Action: {reco.get('action')}, Confidence: {reco.get('confidence')}" if reco else "N/A",
                "actual_outcome": "",
                "deviation": "",
                "mistakes": [],
                "lessons": [{"lesson_type": "timing", "lesson_text": ""}],
                "new_rule_candidate": ""
            }
            return skeleton
        finally:
            conn.close()

    @staticmethod
    def submit_review(review_data: dict):
        """提交复盘并持久化 (DB + Wiki)"""
        conn = get_db_connection(read_only=False)
        try:
            review_id = review_data.get("review_id", make_id("rev"))
            now = datetime.now()
            
            # 1. 写入 DB
            import json
            conn.execute(
                """
                INSERT INTO performance_reviews (
                    review_id, linked_report_id, linked_recommendation_id, symbol,
                    expected_outcome, actual_outcome, deviation, mistake_tags,
                    lessons_json, new_rule_candidate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id, review_data["linked_report_id"], review_data.get("linked_recommendation_id"),
                    review_data["symbol"], review_data["expected_outcome"], review_data["actual_outcome"],
                    review_data["deviation"], ",".join(review_data.get("mistakes", [])),
                    json.dumps(review_data["lessons"]), review_data.get("new_rule_candidate"), now
                )
            )

            # 2. 更新建议的复盘状态
            if review_data.get("linked_recommendation_id"):
                conn.execute(
                    "UPDATE recommendations SET review_status = 'reviewed' WHERE recommendation_id = ?",
                    [review_data["linked_recommendation_id"]]
                )

            # 3. 导出至 Wiki (标准化模板)
            ReviewService._export_to_wiki(review_data, now)
            
            return review_id
        finally:
            conn.close()

    @staticmethod
    def _export_to_wiki(data: dict, timestamp: datetime):
        """标准化 Wiki Markdown 导出"""
        content = f"""# Performance Review: {data['symbol']} ({data['review_id']})

## Summary
Execution post-mortem for report {data['linked_report_id']}.

## Linked Recommendation
- **ID**: {data.get('linked_recommendation_id', 'N/A')}
- **Expected Outcome**: {data['expected_outcome']}

## Actual Outcome
{data['actual_outcome'] or 'Pending verification.'}

## Deviation
{data['deviation'] or 'N/A'}

## Mistakes
{", ".join(data.get('mistakes', [])) if data.get('mistakes') else 'None identified.'}

## Lessons Learned
{chr(10).join([f"- **[{l['lesson_type']}]**: {l['lesson_text']}" for l in data['lessons']])}

## New Rule Candidate
> {data.get('new_rule_candidate') or 'No new rules proposed at this stage.'}
"""
        ObjectService.save_wiki_object(
            category="reviews",
            name=f"review_{data['symbol'].replace('/', '_')}_{timestamp.strftime('%Y%m%d_%H%M')}",
            content=content,
            frontmatter={
                "review_id": data["review_id"],
                "report_id": data["linked_report_id"],
                "symbol": data["symbol"],
                "created_at": timestamp.isoformat()
            }
        )
