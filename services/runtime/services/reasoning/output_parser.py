import json
import re
import logging
from typing import Any, Dict, Optional
from pydantic import ValidationError
from .models import ReasoningResult

logger = logging.getLogger(__name__)

class ReasoningParser:
    """推理结果解析器 - 负责从 LLM 原始文本中提取并归一化结构化数据"""

    def __init__(self):
        # 预定义别名映射，用于将不同模型的口语化输出归一化为宪法字段
        self.alias_map = {
            "pros": "evidence_for",
            "cons": "evidence_against",
            "recommendation": "action",
            "recommendations": "next_steps",
            "confidence_score": "confidence",
            "thesis_summary": "summary",
            "findings": "key_findings",
            "action_type": "action"
        }

    def parse(self, raw_text: str) -> Optional[ReasoningResult]:
        """将原始文本解析为 ReasoningResult 对象"""
        try:
            # 1. 提取 JSON 块
            json_str = self._extract_json_block(raw_text)
            if not json_str:
                logger.error("No JSON block found in LLM output")
                return None

            # 2. 基础反序列化
            data = json.loads(json_str)

            # 3. 递归归一化字段别名
            normalized_data = self._normalize_data(data)

            # 4. Pydantic 校验与实例化
            # 注入原始文本用于调试
            if "raw_output" not in normalized_data:
                normalized_data["raw_output"] = raw_text

            return ReasoningResult.model_validate(normalized_data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            # 这里可以根据严重程度决定是否返回部分填充的对象（软降级）
            # 目前采取严谨策略，返回 None 让上层处理失败
            return None
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            return None

    def _extract_json_block(self, text: str) -> Optional[str]:
        """从带有噪音的文本中提取 JSON 块"""
        # 优先匹配 Markdown 代码块
        code_block_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # 其次尝试匹配首个 { 和 最后一个 } 之间的内容
        bracket_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if bracket_match:
            return bracket_match.group(1).strip()
        
        return None

    def _normalize_data(self, data: Any) -> Any:
        """递归应用别名映射进行归一化"""
        if isinstance(data, list):
            return [self._normalize_data(item) for item in data]
        
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                # 转换键名
                normalized_key = self.alias_map.get(k.lower(), k)
                # 递归处理值（如果是嵌套 dict/list）
                new_data[normalized_key] = self._normalize_data(v)
            
            # 特殊处理：将顶层的 pros/cons 映射到内部的 thesis
            if "evidence_for" in new_data and "thesis" in new_data:
                if "evidence_for" not in new_data["thesis"]:
                    new_data["thesis"]["evidence_for"] = new_data.pop("evidence_for")
            
            if "evidence_against" in new_data and "thesis" in new_data:
                if "evidence_against" not in new_data["thesis"]:
                    new_data["thesis"]["evidence_against"] = new_data.pop("evidence_against")

            return new_data
        
        return data
