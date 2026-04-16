from __future__ import annotations
from typing import Any, Literal, List, Optional
from pydantic import BaseModel, Field

class MarketThesis(BaseModel):
    """市场论点模型 - 核心判断本体"""
    summary: str = Field(..., description="对当前市场状况的高度概括")
    key_findings: List[str] = Field(default_factory=list, description="关键发现或观测到的核心事实")
    evidence_for: List[str] = Field(default_factory=list, description="支持当前建议的多头/看涨证据或有利因素")
    evidence_against: List[str] = Field(default_factory=list, description="对抗当前建议的空头/看跌风险或不利因素")
    confidence: float = Field(..., ge=0.0, le=1.0, description="推理置信度 (0.0-1.0)")
    timeframe: Optional[str] = Field(None, description="该判断适用的时间周期")
    sentiment_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="情绪评分 (0-10)")

class ExecutionAction(BaseModel):
    """执行建议模型 - 核心建议动作"""
    action: Literal["observe", "hold", "accumulate", "reduce", "exit", "avoid"] = Field(
        ..., description="建议的具体操作类型"
    )
    position_size_pct: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="建议的仓位占资产百分比"
    )
    stop_loss: Optional[float] = Field(None, description="建议止损价位")
    take_profit: Optional[float] = Field(None, description="建议止盈价位")
    invalidation_condition: Optional[str] = Field(
        None, description="该建议逻辑失效的触发条件（例如跌破某个关键位）"
    )

class ReasoningResult(BaseModel):
    """完整推理结果模型 - 聚合分析与建议"""
    thesis: MarketThesis = Field(..., description="市场分析论点")
    action_plan: ExecutionAction = Field(..., description="执行建议方案")
    risk_flags: List[str] = Field(default_factory=list, description="由 AI 识别并打上的风险标签")
    next_steps: List[str] = Field(default_factory=list, description="建议的后续具体操作步骤")
    raw_output: Optional[str] = Field(None, description="调试用的模型原始输出文本")
    provider_metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="底层模型提供商的元数据（Token消耗、延迟等）"
    )
