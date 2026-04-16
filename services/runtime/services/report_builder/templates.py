from __future__ import annotations
from services.report_builder.utils import format_timestamp, list_to_md

def build_8_section_report(data: dict) -> str:
    """构建 PFIOS 标准 8 段式报告"""
    
    sections = []
    
    # 1. Title
    title = data.get("title", "PFIOS Intelligence Brief")
    sections.append(f"# {title}\n")
    
    # 2. Executive Summary
    sections.append("## 📝 Executive Summary\n")
    sections.append(f"{data.get('summary', 'No summary provided.')}\n")
    
    # 3. Context
    sections.append("## 🔍 Context\n")
    ctx = data.get("context", {})
    sections.append(f"- **Generated At**: {format_timestamp(data.get('metadata', {}).get('generated_at'))}")
    sections.append(f"- **Asset**: {ctx.get('symbol', 'Global')}")
    sections.append(f"- **Sources**: {', '.join(ctx.get('sources', ['Unknown']))}\n")
    
    # 4. Key Findings
    sections.append("## 💡 Key Findings\n")
    sections.append(list_to_md(data.get("key_findings", [])) + "\n")
    
    # 5. Supporting Evidence
    sections.append("## ✅ Supporting Evidence\n")
    sections.append(list_to_md(data.get("evidence_for", [])) + "\n")
    
    # 6. Contradictions / Risks (预留风控挂口)
    sections.append("## ⚠️ Contradictions & Risks\n")
    sections.append(list_to_md(data.get("evidence_against", [])))
    risk_flags = data.get("risk_flags", [])
    if risk_flags:
        sections.append("\n> [!CAUTION]\n> **Risk Flags Detected**\n" + 
                        "\n".join([f"> - {f}" for f in risk_flags]))
    sections.append("\n")
    
    # 7. Recommendations
    sections.append("## 🚀 Recommendations\n")
    sections.append(list_to_md(data.get("recommendations", [])) + "\n")
    
    # 8. Next Steps
    sections.append("## ⏭️ Next Steps\n")
    sections.append(list_to_md(data.get("next_actions", [])) + "\n")
    
    return "\n".join(sections)
