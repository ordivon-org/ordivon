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

from pfios.orchestrator.engine import PFIOSOrchestrator
from pfios.core.config.settings import settings

async def run_full_test():
    print("=== PFIOS Full Loop Smoke Test ===")
    
    # 强制设置 Mock 模式以确保安全和确定性
    settings.reasoning_provider = "mock"
    settings.auto_execute = True
    settings.dry_run = True  # 必须开启，否则会尝试真实下单
    
    orchestrator = PFIOSOrchestrator()
    
    symbol = "BTC/USDT"
    query = "分析当前 BTC 走势并给出操作建议"
    
    print(f"\n[1] Starting analysis for {symbol}...")
    try:
        # PFIOS 现在主要使用 execute_analyze_and_suggest 作为入口
        result = await orchestrator.execute_analyze_and_suggest(symbol, query)
        
        print("\n[2] Execution Result Summary:")
        print(f"    Symbol:    {result.get('symbol', 'N/A')}")
        print(f"    Decision:  {result.get('decision', 'N/A')}")
        
        if result.get('execution'):
            print(f"    Execution: {result['execution'].get('status')} ({result['execution'].get('reason', 'N/A')})")
        else:
            print("    Execution: Not triggered (Decision might not be ALLOW)")

        print("\n[3] Reasoning Summary:")
        if 'thesis' in result:
            print(f"    Thesis: {result['thesis'].get('summary', 'No summary')}")
            print(f"    Confidence: {result['thesis'].get('confidence', 'N/A')}")
        
        # 验证
        assert "decision" in result
        assert "thesis" in result
        print("\n[SUCCESS] Smoke Test PASSED!")
        
    except Exception as e:
        print(f"\n[FAILURE] Smoke Test FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 尽量避免在终端使用 Unicode 字符，防止 GBK 编码错误
    asyncio.run(run_full_test())
