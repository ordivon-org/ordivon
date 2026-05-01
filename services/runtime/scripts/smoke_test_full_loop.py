"""
scripts/smoke_test_full_loop.py — PFIOS 终端到终端全链路闭环测试
测试：上下文加载 -> 推理引擎 -> 治理决策 -> (Mock) 执行
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.runtime.engine import PFIOSOrchestrator
from shared.config.settings import settings
from domains.research.models import AnalysisRequest
from state.db.session import SessionLocal


async def run_full_test():
    print("=== PFIOS Full Loop Smoke Test ===")

    # 强制设置 Mock 模式以确保安全和确定性
    settings.reasoning_provider = "mock"

    orchestrator = PFIOSOrchestrator()

    symbol = "BTC-USDT"
    query = "分析当前 BTC 走势并给出操作建议"

    print(f"\n[1] Starting analysis for {symbol}...")
    db = SessionLocal()
    try:
        # PFIOS 现在主要使用 execute_analyze 作为入口
        result = orchestrator.execute_analyze(AnalysisRequest(query=query, symbol=symbol, timeframe="4h"), db=db)

        print("\n[2] Execution Result Summary:")
        print(f"    Analysis ID: {result.get('analysis_id', 'N/A')}")
        print(f"    Governance:  {'ALLOWED' if result.get('governance', {}).get('allowed') else 'BLOCKED'}")

        print("\n[3] Reasoning Summary:")
        print(f"    Thesis: {result.get('thesis', 'No thesis')}")
        print(f"    Summary: {result.get('summary', 'No summary')}")

        # 验证
        assert "analysis_id" in result
        assert "thesis" in result
        print("\n[SUCCESS] Smoke Test PASSED!")

    except Exception as e:
        print(f"\n[FAILURE] Smoke Test FAILED: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # 尽量避免在终端使用 Unicode 字符，防止 GBK 编码错误
    asyncio.run(run_full_test())
