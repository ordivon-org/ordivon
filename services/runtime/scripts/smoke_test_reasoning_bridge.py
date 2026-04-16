import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录加入 PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

from apps.api.app.core.config import settings
from services.orchestrator.engine import PFIOSOrchestrator
from services.reasoning import ReasoningResult, ReasoningInvocationError, ReasoningParseError

async def run_smoke_test():
    print("=== PFIOS Step 8.2 Reasoning Bridge Smoke Test ===\n")
    
    orchestrator = PFIOSOrchestrator()
    symbol = "BTC/USDT"
    query = "分析当前 BTC 的价格走势并给出操作建议。"

    # --- Case 1: Mock Mode (Baseline) ---
    print("--- Case 1: Mock Reasoning (Verify Fallback) ---")
    settings.reasoning_provider = "mock"
    try:
        result = await orchestrator.execute_analyze_and_suggest(symbol, query)
        print(f"Result Status: {result['status']}")
        print(f"Summary: {result['thesis']['summary']}")
        print(f"Decision: {result['decision']}\n")
    except Exception as e:
        print(f"Mock Case Failed: {e}\n")

    # --- Case 2: Real Hermes CLI (Happy Path) ---
    print("--- Case 2: Real Hermes CLI (Substrate Bridge) ---")
    settings.reasoning_provider = "hermes_cli"
    # 注意: 这里依赖本地已安装的 hermes-runtime 且配置了有效的模型
    try:
        print("Invoking real LLM substrate (this may take a few seconds)...")
        result = await orchestrator.execute_analyze_and_suggest(symbol, query)
        print(f"Result Status: {result['status']}")
        print(f"Summary: {result['thesis']['summary']}")
        print(f"Action: {result['action']['action'] if result['action'] else 'NONE'}")
        print(f"Decision: {result['decision']}\n")
    except ReasoningInvocationError as e:
        print(f"X Invocation Error (Expected if Hermes env is not ready): {e}\n")
    except ReasoningParseError as e:
        print(f"X Parse Error (LLM output was not valid JSON): {e}\n")
    except Exception as e:
        print(f"X Unexpected Error: {e}\n")

    # --- Case 3: Timeout Simulation ---
    print("--- Case 3: Timeout Handling ---")
    settings.hermes_timeout_seconds = 1  # 故意设置极短超时
    try:
        await orchestrator.execute_analyze_and_suggest(symbol, query)
    except ReasoningInvocationError as e:
        print(f"OK: Correctly caught timeout as ReasoningInvocationError: {e}\n")
    except Exception as e:
        print(f"X Wrong error type for timeout: {type(e).__name__}: {e}\n")

    print("=== Smoke Test Finished ===")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
