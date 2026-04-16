import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.api.app.core.config import settings

class FailureRecorder:
    """失败样本记录器 (Failure Corpus Substrate) - 负责固化坏样本以供后续评估与调优"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.get_abs_path("data/evals/failures"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def record_failure(
        self,
        failure_type: str, # model|context|parser|governance|mixed
        input_context: Dict[str, Any],
        raw_output: str,
        parsed_result: Optional[Dict[str, Any]] = None,
        risk_decision: str = "unknown",
        problem_notes: Optional[List[str]] = None
    ) -> str:
        """记录一条失败样本"""
        failure_id = f"fail_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        failure_entry = {
            "failure_id": failure_id,
            "timestamp": datetime.now().isoformat(),
            "failure_type": failure_type,
            "input_context_summary": input_context,
            "raw_output": raw_output,
            "parsed_result": parsed_result,
            "risk_decision": risk_decision,
            "problem_notes": problem_notes or [],
            "suggested_fix": [] # 留给人工复盘填写
        }

        file_path = self.storage_dir / f"{failure_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(failure_entry, f, indent=2, ensure_ascii=False)
            
        return failure_id
