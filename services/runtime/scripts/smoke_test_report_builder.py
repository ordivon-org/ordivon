import sys
import os
from pathlib import Path

# 将相关路径加入 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "apps" / "api"))
sys.path.append(str(BASE_DIR))

from services.report_builder.build_markdown import ReportBuilder
from app.services.object_service import ObjectService

def test_report_pipeline():
    print("=== PFIOS Report Builder Smoke Test ===")
    
    # 1. Prepare Mock Analysis Data (Structured Contract)
    mock_data = {
        "report_type": "analyze_and_suggest",
        "title": "BTC_Alpha_Strategy_Review",
        "summary": "BTC shows strong support at 65k markers. Bias remains bullish.",
        "context": {
            "symbol": "BTC/USDT",
            "sources": ["Binance_Spot", "System_Harness"]
        },
        "key_findings": [
            "Market structure is bullish on 4H",
            "Support holding firm"
        ],
        "evidence_for": [
            "Golden Cross on move",
            "Volume increasing"
        ],
        "evidence_against": [
            "Overbought on 1H",
            "Macro resistance ahead"
        ],
        "risk_flags": [
            "High volatility event in 2h",
            "Low liquidity in order book"
        ],
        "recommendations": [
            "Long on breakout",
            "Tight SL at 64,500"
        ],
        "next_actions": [
            "Monitor 68k breakout",
            "Review bias in 12h"
        ],
        "metadata": {
            "generated_at": "2026-04-16T22:45:00",
            "engine_version": "v0.1-PFIOS"
        }
    }
    
    # 2. Render to Markdown
    print("Rendering report...")
    render_result = ReportBuilder.render(mock_data)
    
    print(f"Rendered Title: {render_result['title']}")
    print(f"Suggested Path: {render_result['suggested_path']}")
    assert "Executive Summary" in render_result["markdown"]
    assert "Risk Flags Detected" in render_result["markdown"]
    
    # 3. Persist to Wiki via ObjectService
    print("Persisting to Wiki...")
    category = f"reports/{render_result['report_type']}"
    file_path_str = ObjectService.save_wiki_object(
        category=category,
        name=render_result["slug"],
        content=render_result["markdown"],
        frontmatter=render_result["metadata"]
    )
    
    final_path = Path(file_path_str)
    print(f"Final Physical Path: {final_path}")
    assert final_path.exists()
    
    # 4. Verify Content
    content = final_path.read_text(encoding="utf-8")
    assert "BTC_Alpha_Strategy_Review" in content
    assert "Bias remains bullish" in content
    
    print("=== REPORT BUILDER CHECKS PASSED ===")

if __name__ == "__main__":
    test_report_pipeline()
