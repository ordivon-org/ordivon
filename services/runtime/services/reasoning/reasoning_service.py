import logging
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from .base_client import BaseLLMClient
from .output_parser import ReasoningParser
from .models import ReasoningResult
from .failure_recorder import FailureRecorder

logger = logging.getLogger(__name__)

class ReasoningError(Exception):
    """推理层基类异常"""
    pass

class ReasoningInvocationError(ReasoningError):
    """子进程调用失败 (超时、崩溃、环境错误) (按约束 5 实现)"""
    pass

class ReasoningParseError(ReasoningError):
    """结果解析失败 (非合法 JSON、结构严重缺失) (按约束 5 实现)"""
    pass


class ReasoningService:
    """推理层核心服务 - 负责跨层调度推理闭环"""

    def __init__(
        self, 
        llm_client: BaseLLMClient, 
        parser: ReasoningParser,
        templates_dir: str,
        default_template: str = "base_analysis.j2",
        failure_recorder: Optional[FailureRecorder] = None
    ):
        self.llm_client = llm_client
        self.parser = parser
        self.default_template_name = default_template
        self.failure_recorder = failure_recorder or FailureRecorder()
        
        # 初始化 Jinja2 环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape()
        )

    def analyze(self, context: Dict[str, Any]) -> ReasoningResult:
        """执行结构化推理分析
        
        流程: Context -> Prompt -> LLM -> Raw -> Parser -> Result
        """
        # 1. 构建 Prompt (按约束修订)
        prompt = self.build_prompt(context)
        
        # 2. 调用 LLM (按约束修订: 区分三类失败)
        raw_response = self.llm_client.generate(prompt)
        
        if not raw_response.ok:
            error_msg = f"LLM Invocation failed (exit={raw_response.exit_code})"
            if raw_response.timed_out:
                error_msg = "LLM Invocation timed out"
            
            logger.error(error_msg)
            raise ReasoningInvocationError(error_msg)

        # 3. 解析结果 (按约束修订: 容错清洗与别名归一化)
        result = self.parser.parse(raw_response.stdout)
        
        if result is None:
            logger.error("Failed to parse LLM structured output")
            # 记录解析失败样本 (按 8.3.4 指令)
            self.failure_recorder.record_failure(
                failure_type="parser",
                input_context=context,
                raw_output=raw_response.stdout,
                problem_notes=["Output format invalid or JSON incomplete"]
            )
            raise ReasoningParseError("The content returned by LLM cannot be parsed into a valid ReasoningResult")

        # 注入元数据
        if not result.provider_metadata:
            result.provider_metadata = {}
        
        result.provider_metadata.update({
            "duration_ms": raw_response.duration_ms,
            "exit_code": raw_response.exit_code
        })

        # 注意: 即使 result.thesis.confidence 很低或 evidence 为空，
        # 解析器也会返回成功的对象。这是为了让 RiskEngine 去做最终裁决 (C 类失败)，
        # 而不是在推理层炸掉。 (对齐约束 5)
        
        return result

    def build_prompt(self, context: Dict[str, Any], template_name: Optional[str] = None) -> str:
        """渲染渲染提示词模板"""
        tpl_name = template_name or self.default_template_name
        template = self.jinja_env.get_template(tpl_name)
        return template.render(**context)
