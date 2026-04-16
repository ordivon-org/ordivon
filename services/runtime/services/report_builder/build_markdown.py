from __future__ import annotations
from typing import Any
from services.report_builder.templates import build_8_section_report
from services.report_builder.utils import slugify

class ReportBuilder:
    """
    通用报告渲染引擎 (Interface Layer) 
    
    合约契约 (Input Contract):
    - report_type: str (e.g. 'analyze_and_suggest')
    - title: str
    - summary: str
    - context: dict {symbol, timeframe, sources}
    - key_findings: list[str]
    - evidence_for: list[str]
    - evidence_against: list[str]
    - risk_flags: list[str]
    - recommendations: list[str]
    - next_actions: list[str]
    - metadata: dict {generated_at, engine_version}
    """

    @staticmethod
    def render(data: dict[str, Any]) -> dict[str, Any]:
        """主渲染入口"""
        
        # 1. 拼装 Markdown 内容
        markdown_content = build_8_section_report(data)
        
        # 2. 生成元数据与物理建议
        title = data.get("title", "Untitled Report")
        report_type = data.get("report_type", "general")
        
        slug = slugify(title)
        suggested_path = f"reports/{report_type}/{slug}.md"
        
        return {
            "markdown": markdown_content,
            "title": title,
            "slug": slug,
            "report_type": report_type,
            "suggested_path": suggested_path,
            "metadata": data.get("metadata", {})
        }
