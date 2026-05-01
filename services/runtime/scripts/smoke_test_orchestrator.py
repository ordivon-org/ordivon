import asyncio
import sys
from pathlib import Path

# 将相关路径加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "apps" / "api"))
sys.path.append(str(BASE_DIR))

from services.orchestrator.engine import PFIOSOrchestrator
from services.orchestrator.router import TaskRouter, WorkflowType


async def test_orchestrator_flow():
    print("=== PFIOS Orchestrator Smoke Test ===")

    # 1. Test Router
    query = "Analyze BTC/USDT and give me your opinion."
    flow_type = TaskRouter.route_query(query)
    print(f"Router Result: {flow_type}")
    assert flow_type == WorkflowType.ANALYZE

    # 2. Test Engine
    engine = PFIOSOrchestrator()
    print("Running analyze_and_suggest workflow...")
    result = await engine.execute_analyze_and_suggest("BTC/USDT", query)

    print(f"Engine Result Status: {result['status']}")
    print(f"Thesis: {result['thesis']}")

    assert result["status"] in ["success", "blocked"]
    assert "thesis" in result
    assert "risk_report" in result

    print("=== ORCHESTRATOR CHECKS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_orchestrator_flow())
