"""
scripts/smoke_test_outcome_loop.py — PFIOS 核心闭环烟雾测试
"""
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, UTC

# 设置路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.environ["PFIOS_ROOT"] = str(project_root)
os.environ["PYTHONPATH"] = str(project_root)

from pfios.core.db.session import get_db_connection
from pfios.orchestrator.recommendation_tracker import RecommendationTracker
from pfios.orchestrator.outcome_detector import OutcomeDetector
from pfios.orchestrator.review_generator import ReviewGenerator
from pfios.domain.recommendation.models import LifecycleStatus

def run_smoke_test():
    print("[START] Starting PFIOS Core Loop Smoke Test...")
    
    conn = get_db_connection(read_only=False)
    try:
        # 1. 模拟生成建议
        print("Step 1: Simulating Recommendation Generation...")
        analysis_data = {
            "decision": "allow",
            "thesis": {"confidence": 0.85},
            "action_plan": {"action": "accumulate"},
            "metadata": {
                "symbol": "BTC/USDT",
                "title": "Smoke Test Recommendation",
                "outcome_metric_type": "price_rule",
                "outcome_metric_config": {
                    "target_price": 70000,
                    "stop_price": 60000
                }
            }
        }
        reco_id = RecommendationTracker.auto_generate_if_needed(analysis_data, "test_report_id")
        if not reco_id:
            print("[FAIL] Failed to generate recommendation.")
            return
        print(f"[OK] Generated Recommendation: {reco_id}")

        # 2. 模拟用户采纳
        print("Step 2: Simulating User Adoption...")
        RecommendationTracker.transition(reco_id, LifecycleStatus.ADOPTED)
        print("[OK] Transitioned to ADOPTED")

        # 3. 注入模拟价格数据
        print("Step 3: Injecting Mock Price Data (To trigger SATISFIED)...")
        conn.execute(
            "INSERT OR REPLACE INTO ohlcv (exchange, symbol, timeframe, ts, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("okx", "BTC/USDT", "1h", int(time.time()*1000), 65000, 71000, 64000, 71000, 100)
        )
        print("[OK] Injected Price: 71000 (Target: 70000)")
        
        # 必须先关闭主链接，因为后边的 detector 会开启自己的链接，DuckDB 不允许多个不同模式的链接同时存在
        conn.close()

        # 4. 运行结果探测
        print("Step 4: Running Outcome Detection...")
        detector = OutcomeDetector()
        detected = detector.run_detection_cycle()
        detector.close()
        
        reco = RecommendationTracker.get_by_id(reco_id)
        print(f"[OK] Detection Cycle Finished. Detected: {detected}")
        print(f"   New Lifecycle Status: {reco['lifecycle_status']}")
        
        if reco['lifecycle_status'] != 'review_pending':
            print(f"[FAIL] Status mismatch! Expected review_pending, got {reco['lifecycle_status']}")
            return

        # 5. 运行复盘生成
        print("Step 5: Running Review Generation...")
        generator = ReviewGenerator()
        generated = generator.run_generation_cycle()
        generator.close()
        
        reco_post = RecommendationTracker.get_by_id(reco_id)
        print(f"[OK] Generation Cycle Finished. Generated Reviews: {generated}")
        print(f"   Review Status: {reco_post['review_status']}")
        
        if reco_post['review_status'] != 'generated':
            print(f"[FAIL] Review Status mismatch! Expected generated, got {reco_post['review_status']}")
            return

        print("\n[WIN] SMOKE TEST PASSED! The PFIOS Core Loop is active.")

    except Exception as e:
        print(f"[ERROR] Smoke test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保在 try 块开头定义的 conn 在这里能安全关闭（如果还没关）
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    run_smoke_test()
