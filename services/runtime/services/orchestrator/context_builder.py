from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from apps.api.app.core.db import get_db_connection

logger = logging.getLogger(__name__)

class ContextBuilder:
    """上下文构建器 (Orchestration Support) - 负责聚合推理所需的五层背景数据 (Step 8.3 重构)"""

    def build_layered_context(self, symbol: str, user_query: str, timeframe: Optional[str] = None) -> Dict[str, Any]:
        """聚合分层上下文主入口"""
        conn = get_db_connection(read_only=True)
        try:
            return {
                "query_context": self._build_query_context(symbol, user_query, timeframe),
                "market_context": self._build_market_context(conn, symbol),
                "portfolio_context": self._build_portfolio_context(conn, symbol),
                "memory_context": self._build_memory_context(conn, symbol),
                "governance_hint": self._build_governance_hint()
            }
        finally:
            conn.close()

    def _build_query_context(self, symbol: str, query: str, timeframe: Optional[str]) -> Dict[str, Any]:
        """构建查询层上下文 (User Intent)"""
        return {
            "user_query": query,
            "symbols": [symbol],
            "timeframe": timeframe or "unknown",
            "analysis_goal": "breakout_validation" if "突破" in query else "market_analysis",
            "workflow": "analyze_and_suggest",
            "timestamp": datetime.now().isoformat()
        }

    def _build_market_context(self, conn: Any, symbol: str) -> Dict[str, Any]:
        """构建市场层上下文 (Market Facts)"""
        # 获取资产属性
        asset = conn.execute("SELECT * FROM assets WHERE symbol = ?", [symbol]).fetchone()
        
        # 获取最近观测
        rows = conn.execute(
            "SELECT content, sentiment FROM observations WHERE symbol = ? ORDER BY created_at DESC LIMIT 5",
            [symbol]
        ).fetchall()
        observations = [f"[{r[1]}] {r[0]}" for r in rows]

        # 获取 OHLCV 简单特征 (模拟计算)
        ohlcv_rows = conn.execute(
            "SELECT close FROM ohlcv WHERE symbol = ? ORDER BY ts DESC LIMIT 20",
            [symbol]
        ).fetchall()
        
        trend_bias = "neutral"
        if len(ohlcv_rows) >= 10:
            prices = [r[0] for r in ohlcv_rows]
            if prices[0] > sum(prices[:10])/10: trend_bias = "bullish"
            elif prices[0] < sum(prices[:10])/10: trend_bias = "bearish"

        return {
            "price_summary": f"Current data for {symbol} loaded.",
            "asset_info": dict(asset) if asset else {},
            "ohlcv_features": {
                "trend_bias": trend_bias,
                "volatility_regime": "stable", # Placeholder
                "volume_pattern": "normal"      # Placeholder
            },
            "regime_hint": "range_bound", # Placeholder
            "event_context": [],            # Placeholder for macro
            "recent_observations": observations
        }

    def _build_portfolio_context(self, conn: Any, symbol: str) -> Dict[str, Any]:
        """构建组合层上下文 (Portfolio Awareness)"""
        position = conn.execute(
            "SELECT * FROM position_states WHERE symbol = ?", [symbol]
        ).fetchone()
        
        return {
            "has_existing_exposure": position is not None,
            "related_positions": [dict(position)] if position else [],
            "portfolio_risk_state": "normal",
            "exposure_hint": "No significant existing exposure" if not position else "Already holding this asset"
        }

    def _build_memory_context(self, conn: Any, symbol: str) -> Dict[str, Any]:
        """构建记忆层上下文 (Historical Experience)"""
        # 提取最近一次成功的或失败的复盘报告
        recent_review = conn.execute(
            "SELECT note_md, action, confidence FROM ai_reviews WHERE signal_id IN (SELECT signal_id FROM signals WHERE symbol = ?) ORDER BY created_at DESC LIMIT 1",
            [symbol]
        ).fetchone()

        return {
            "similar_case_summary": recent_review[0] if recent_review else None,
            "recent_relevant_failure": None, # Placeholder
            "most_relevant_rule_of_thumb": "Market usually consolidates after high volume spikes." if symbol.endswith("USDT") else None
        }

    def _build_governance_hint(self) -> Dict[str, Any]:
        """构建治理提示层 (Governance Discipline - 按约束修订)"""
        return {
            "analysis_discipline": [
                "1. 必须同时呈现场向支持证据与反向风险因素 (MUST present evidence_for AND evidence_against)",
                "2. 在不确定性较高时必须采取保守立场 (Be conservative under uncertainty)",
                "3. 严禁过度解读短期噪声为长期趋势 (Avoid overstating conviction)",
                "4. 必须输出合法的 JSON 格式"
            ],
            "action_bias_hint": "在多空证据冲突或关键数据不足时，优先给与 observe (观察) 或 avoid (规避) 建议。",
            "forbidden_behaviors": [
                "在没有确凿证据的情况下输出高仓位建议",
                "在分析报告中忽略已知的宏观风险"
            ]
        }
