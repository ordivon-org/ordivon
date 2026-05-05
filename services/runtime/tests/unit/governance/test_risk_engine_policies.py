import pytest
from domains.research.models import AnalysisResult
from governance_engine.risk_engine.engine import RiskEngine
from datetime import datetime


class TestRiskEnginePolicies:
    @pytest.fixture
    def risk_engine(self):
        return RiskEngine()

    def test_allow_bitcoin_analysis(self, risk_engine):
        # Case: BTC (Not forbidden)
        analysis = AnalysisResult(
            id="ana_001",
            query="Analyze BTC",
            symbol="BTC-USDT",
            timeframe="4h",
            summary="Bullish outlook",
            thesis="Consolidation break",
            suggested_actions=["ACCUMULATE"],
            metadata={},
            created_at=datetime.now(),
        )

        decision = risk_engine.validate_analysis(analysis)

        assert decision.decision == "execute"
        assert decision.allowed is True
        assert decision.source == "risk_engine.default_validation"
        assert "Passed" in decision.reasons[0]

    def test_block_pepe_meme_analysis(self, risk_engine):
        # Case: PEPE (In forbidden list)
        analysis = AnalysisResult(
            id="ana_002",
            query="Analyze PEPE",
            symbol="PEPE/USDT",
            timeframe="1h",
            summary="Very Moon",
            thesis="Speculation",
            suggested_actions=["BUY"],
            metadata={},
            created_at=datetime.now(),
        )

        decision = risk_engine.validate_analysis(analysis)

        assert decision.decision == "reject"
        assert decision.allowed is False
        assert decision.source == "risk_engine.forbidden_symbols_policy"
        assert any("PEPE" in r and "blocked" in r for r in decision.reasons)

    def test_block_general_meme_substring(self, risk_engine):
        # Case: Any symbol containing "MEME"
        analysis = AnalysisResult(
            id="ana_003",
            query="Analyze something meme",
            symbol="SOME-MEME-COIN",
            timeframe="1h",
            summary="Meme party",
            thesis="Hype",
            suggested_actions=["BUY"],
            metadata={},
            created_at=datetime.now(),
        )

        decision = risk_engine.validate_analysis(analysis)

        assert decision.decision == "reject"
        assert decision.allowed is False
        assert any("MEME" in r for r in decision.reasons)

    def test_block_no_actions(self, risk_engine):
        # Case: No suggested actions (Default RiskEngine safety)
        analysis = AnalysisResult(
            id="ana_004",
            query="Analyze BTC",
            symbol="BTC-USDT",
            timeframe="4h",
            summary="Unclear",
            thesis="Wait",
            suggested_actions=[],  # EMPTY
            metadata={},
            created_at=datetime.now(),
        )

        decision = risk_engine.validate_analysis(analysis)

        assert decision.decision == "escalate"
        assert decision.allowed is False
        assert decision.source == "risk_engine.default_validation"
        assert "No suggested actions" in decision.reasons[0]
