from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class RawLLMResponse:
    """底层 LLM 调用原始响应模型"""
    ok: bool = False
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: int = 0
    timed_out: bool = False  # 显式超时状态 (按约束 2 添加)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseLLMClient:
    """推理客户端抽象基类 (Adapter Pattern)"""
    
    def generate(self, prompt: str, **kwargs) -> RawLLMResponse:
        """发起推理请求
        
        Args:
            prompt: 发送给模型的完整提示词
            **kwargs: 扩展参数 (如 model_profile, timeout 等)
            
        Returns:
            RawLLMResponse: 包含执行结果与元数据的原始响应
        """
        raise NotImplementedError("Subclasses must implement generate()")
