#!/usr/bin/env python3
"""Capture governance trace events to traces/ directory.

Writes timestamped JSON trace files. Use from any governance activity
(workflow steps, checker runs, receipt generation) to record what happened.

Usage:
    from scripts.capture_trace import capture_trace
    
    capture_trace("reconciliation", {
        "step": "validate_registry",
        "status": "completed",
        "duration_ms": 234
    })
    
    # Also works as CLI:
    python scripts/capture_trace.py --event reconciliation --data '{"step":"validate","status":"ok"}'
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = ROOT / "traces"


def capture_trace(event_type: str, data: dict) -> Path:
    """Write a trace event to traces/<event_type>/<timestamp>.json"""
    now = datetime.now(timezone.utc)
    event_dir = TRACES_DIR / event_type
    event_dir.mkdir(parents=True, exist_ok=True)
    
    trace = {
        "event_type": event_type,
        "timestamp": now.isoformat(),
        "trace_id": now.strftime("%Y%m%d-%H%M%S-") + event_type,
        "data": data,
    }
    
    filename = now.strftime("%Y%m%d-%H%M%S-%f") + ".json"
    path = event_dir / filename
    path.write_text(json.dumps(trace, indent=2, ensure_ascii=False))
    return path


def list_traces(event_type: str = None) -> list[Path]:
    """List trace files, optionally filtered by event type."""
    if event_type:
        pattern = TRACES_DIR / event_type / "*.json"
    else:
        pattern = TRACES_DIR / "**" / "*.json"
    return sorted(Path(p) for p in TRACES_DIR.glob(str(pattern)) if p.is_file())


if __name__ == "__main__":
    if "--event" in sys.argv and "--data" in sys.argv:
        idx_e = sys.argv.index("--event")
        idx_d = sys.argv.index("--data")
        event_type = sys.argv[idx_e + 1]
        data = json.loads(sys.argv[idx_d + 1])
        path = capture_trace(event_type, data)
        print(f"Trace written: {path}")
    elif "--list" in sys.argv:
        event_filter = sys.argv[2] if len(sys.argv) > 2 else None
        traces = list_traces(event_filter)
        print(f"{len(traces)} trace(s):")
        for t in traces[-20:]:
            print(f"  {t.relative_to(TRACES_DIR)}")
    else:
        print("Usage:")
        print("  python scripts/capture_trace.py --event <type> --data '<json>'")
        print("  python scripts/capture_trace.py --list [event_type]")
