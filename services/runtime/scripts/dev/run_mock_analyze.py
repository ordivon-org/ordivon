from pfios.orchestrator.engine import PFIOSOrchestrator
from pfios.domain.analysis.models import AnalysisRequest


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
