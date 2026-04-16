import json
import sys
from pathlib import Path
from typing import Dict, Any, List

class EvalComparator:
    """差异对比与发布门禁 (Diff Gate Substrate) - 负责决策推理引擎是否允许发布 (Step 8.4.4)"""

    def compare(self, candidate_run_path: str, baseline_path: str) -> Dict[str, Any]:
        with open(candidate_run_path, "r", encoding="utf-8") as f:
            candidate = json.load(f)
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        logger_info = f"Comparing Run {candidate['run_id']} against Baseline {baseline.get('baseline_id', 'unknown')}"
        print(f"=== {logger_info} ===")

        findings = []
        status = "PASS"

        # 1. 指标门禁 (Metrics Check)
        c_stats = candidate["summary"]
        b_metrics = baseline["metrics"]

        # 解析失败率门禁
        if c_stats["parse_failure_rate"] > b_metrics["max_parse_failure_rate"]:
            findings.append(f"FAIL: Parse failure rate {c_stats['parse_failure_rate']} exceeds baseline {b_metrics['max_parse_failure_rate']}")
            status = "FAIL"

        # 结构完整度门禁
        if c_stats["avg_total_score"] < b_metrics["min_structure_score"] - 0.1: # 允许少量波动
            findings.append(f"WARN: Average quality score {c_stats['avg_total_score']} is lower than baseline goal.")
            if status != "FAIL": status = "WARN"

        # 过激建议率门禁
        if c_stats["aggressive_action_rate"] > b_metrics["max_aggressive_action_rate"]:
            findings.append(f"FAIL: Aggressive action rate {c_stats['aggressive_action_rate']} exceeds limit {b_metrics['max_aggressive_action_rate']}")
            status = "FAIL"

        # 2. Case-level Diff (简版)
        # 这里应该对比每个 case 的变化，尤其是 action family 是否发生了漂移
        # 为了演示，我们只在结果中列出总体差异
        
        print(f"Decision: [{status}]")
        for f in findings:
            print(f" - {f}")
            
        return {
            "status": status,
            "findings": findings,
            "candidate_id": candidate["run_id"],
            "baseline_id": baseline.get("baseline_id")
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_eval_runs.py <candidate_run_json> <baseline_json>")
        sys.exit(1)
        
    comparator = EvalComparator()
    comparator.compare(sys.argv[1], sys.argv[2])
