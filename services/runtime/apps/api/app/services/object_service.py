import yaml
from datetime import datetime
from pathlib import Path
from app.core.db import get_db_connection
from app.core.config import settings
from app.utils.crypto import make_id

class ObjectService:
    """核心对象服务 (Knowledge Layer) - 负责 DB 持久化与 Wiki 归档"""

    @staticmethod
    def add_asset(symbol: str, asset_class: str, exchange: str, risk_level: int = 5, metadata: dict = None):
        """记录资产元数据 (DB)"""
        conn = get_db_connection(read_only=False)
        try:
            conn.execute(
                """
                INSERT INTO assets (symbol, asset_class, exchange, risk_level, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (symbol) DO UPDATE SET 
                    exchange=EXCLUDED.exchange, 
                    risk_level=EXCLUDED.risk_level,
                    metadata_json=EXCLUDED.metadata_json
                """,
                (symbol, asset_class, exchange, risk_level, json_dumps(metadata or {}), datetime.now())
            )
        finally:
            conn.close()

    @staticmethod
    def add_observation(symbol: str, content: str, sentiment: float, source: str):
        """记录观测数据 (DB)"""
        conn = get_db_connection(read_only=False)
        try:
            obs_id = make_id("obs")
            conn.execute(
                """
                INSERT INTO observations (obs_id, symbol, content, sentiment, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (obs_id, symbol, content, sentiment, source, datetime.now())
            )
        finally:
            conn.close()

    @staticmethod
    def save_wiki_object(category: str, name: str, content: str, frontmatter: dict):
        """
        创建并存档 Wiki 对象 (Markdown + Frontmatter)
        category: journals/trades/reviews/strategies/research
        """
        wiki_root = settings.wiki_abs_root
        target_dir = wiki_root / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = f"{name}.md"
        file_path = target_dir / file_name
        
        # 构建 Markdown 内容 (带 Frontmatter)
        fm_yaml = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
        full_content = f"---\n{fm_yaml}---\n\n{content}"
        
        file_path.write_text(full_content, encoding="utf-8")
        return str(file_path)

    @staticmethod
    def register_strategy(name: str, logic_md: str, market_regime: str = "Unknown"):
        """注册策略并同步至 Wiki"""
        conn = get_db_connection(read_only=False)
        try:
            strategy_id = make_id("strat")
            now = datetime.now()
            conn.execute(
                """
                INSERT INTO strategies (strategy_id, name, logic_md, market_regime, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (strategy_id, name, logic_md, market_regime, "active", now, now)
            )
            
            # 同时同步至 Wiki
            ObjectService.save_wiki_object(
                category="strategies",
                name=name.lower().replace(" ", "_"),
                content=logic_md,
                frontmatter={
                    "strategy_id": strategy_id,
                    "name": name,
                    "market_regime": market_regime,
                    "created_at": now.isoformat()
                }
            )
            return strategy_id
        finally:
            conn.close()

    @staticmethod
    def get_recent_reports(limit: int = 10) -> list[dict]:
        """获取最近的 AI 推研报告"""
        conn = get_db_connection(read_only=True)
        try:
            # 联合查询 ai_reviews 及其对应的 signals
            query = """
                SELECT r.review_id as report_id, s.symbol, s.strategy_name as title, 
                       r.action as status, r.created_at, 'wiki/reports/' as report_path
                FROM ai_reviews r
                JOIN signals s ON r.signal_id = s.signal_id
                ORDER BY r.created_at DESC
                LIMIT ?
            """
            result = conn.execute(query, [limit])
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row)) for row in result.fetchall()]
        finally:
            conn.close()

# 辅助导入
from app.utils.crypto import json_dumps
