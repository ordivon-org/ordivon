from orchestrator.runtime.engine import PFIOSOrchestrator
from domains.research.models import AnalysisRequest


def main():
    orchestrator = PFIOSOrchestrator()
    result = orchestrator.execute_analyze(
        AnalysisRequest(
            query="Analyze BTC current market structure",
            symbol="BTC-USDT",
            timeframe="4h",
        )
    )
    print(result)


if __name__ == "__main__":
    main()
