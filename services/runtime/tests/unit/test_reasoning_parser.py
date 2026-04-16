import pytest
from services.reasoning import ReasoningParser

def test_parser_standard_json():
    """测试标准 JSON 解析"""
    parser = ReasoningParser()
    raw = """
    {
        "thesis": {
            "summary": "Bullish trend",
            "confidence": 0.8,
            "evidence_for": ["Volume up"],
            "evidence_against": []
        },
        "action_plan": {
            "action": "accumulate",
            "position_size_pct": 10.0
        },
        "risk_flags": ["VOLATILITY"],
        "next_steps": ["Check support"]
    }
    """
    result = parser.parse(raw)
    assert result is not None
    assert result.thesis.summary == "Bullish trend"
    assert result.action_plan.action == "accumulate"

def test_parser_markdown_noise():
    """测试带 Markdown 围栏和前后噪音的解析"""
    parser = ReasoningParser()
    raw = """
    Here is my thought process...
    ```json
    {
        "thesis": {
            "summary": "Consolidating",
            "confidence": 0.5,
            "evidence_for": [],
            "evidence_against": []
        },
        "action_plan": {
            "action": "observe"
        }
    }
    ```
    I hope this helps!
    """
    result = parser.parse(raw)
    assert result is not None
    assert result.thesis.summary == "Consolidating"
    assert result.action_plan.action == "observe"

def test_parser_alias_normalization():
    """测试字段别名归一化 (pros/cons -> evidence_for/against)"""
    parser = ReasoningParser()
    raw = """
    {
        "thesis": {
            "summary": "Mixed outlook",
            "confidence": 0.7,
            "pros": ["Institutional buying"],
            "cons": ["High inflation"]
        },
        "action_plan": {
            "recommendation": "hold"
        }
    }
    """
    result = parser.parse(raw)
    assert result is not None
    assert "Institutional buying" in result.thesis.evidence_for
    assert "High inflation" in result.thesis.evidence_against
    assert result.action_plan.action == "hold"

def test_parser_invalid_json():
    """测试非法 JSON 处理"""
    parser = ReasoningParser()
    raw = "Not a json at all"
    result = parser.parse(raw)
    assert result is None

def test_parser_missing_critical_fields():
    """测试关键字段缺失校验"""
    parser = ReasoningParser()
    # 缺少 confidence
    raw = """
    {
        "thesis": {
            "summary": "No confidence field"
        },
        "action_plan": {
            "action": "hold"
        }
    }
    """
    result = parser.parse(raw)
    assert result is None
