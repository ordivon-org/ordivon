import subprocess
import time
import logging
import json
from typing import List, Optional, Any, Dict
from .base_client import BaseLLMClient, RawLLMResponse

logger = logging.getLogger(__name__)

class HermesCLIClient(BaseLLMClient):
    """Hermes CLI 推理客户端 - 通过子进程物理隔离调用外部推理基座"""

    def __init__(
        self, 
        python_executable: str, 
        runtime_path: str, 
        timeout_seconds: int = 60
    ):
        """
        Args:
            python_executable: 外部 Hermes 环境的 python.exe 路径
            runtime_path: hermes-runtime 的根目录路径
            timeout_seconds: 单次推理超时限制 (按约束 2/5 实现)
        """
        self.python_executable = python_executable
        self.runtime_path = runtime_path
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, **kwargs) -> RawLLMResponse:
        """
        执行单轮推理命令: python cli.py -q "<prompt>"
        (按约束 1 使用 list argv 确保安全与转义正确)
        """
        start_time = time.perf_counter()
        
        # 构造命令行参数列表 (按约束 1: 不使用 shell=True, 不使用拼接字符串)
        cmd = [
            self.python_executable,
            "cli.py",
            "-q",
            prompt
        ]
        
        # 注入环境变量
        env_overrides = {
            **subprocess.os.environ,
            "HERMES_QUIET": "1",
            "PYTHONPATH": ".",
        }

        try:
            logger.info(f"Invoking Hermes CLI substrate: {self.python_executable}")
            
            # 执行子进程
            process = subprocess.run(
                cmd,
                cwd=self.runtime_path,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env_overrides,
                shell=False
            )

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            return RawLLMResponse(
                ok=(process.returncode == 0),
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                timed_out=False,
                metadata={
                    "cmd": " ".join(cmd) if kwargs.get("include_cmd_in_meta") else "HIDDEN"
                }
            )

        except subprocess.TimeoutExpired as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Hermes CLI call timed out after {self.timeout_seconds}s")
            return RawLLMResponse(
                ok=False,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                exit_code=-1,
                duration_ms=duration_ms,
                timed_out=True,
                metadata={"error": "TimeoutExpired"}
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Unexpected error during Hermes CLI invocation: {str(e)}")
            return RawLLMResponse(
                ok=False,
                stderr=str(e),
                stdout="",
                exit_code=-1,
                duration_ms=duration_ms,
                timed_out=False,
                metadata={"error": "ProcessFailure"}
            )

class MockLLMClient(BaseLLMClient):
    """Mock 推理客户端 (满足约束 6, 支持 8.4 回归运行)"""
    def generate(self, prompt: str, **kwargs) -> RawLLMResponse:
        # 这里返回一串预定义的、符合 ReasoningResult 格式的字符串
        mock_json = {
            "thesis": {
                "summary": "Mock Analysis: Trending upwards with caution.",
                "evidence_for": ["Price > MA20"],
                "evidence_against": ["RSI Overbought"],
                "confidence": 0.8,
                "key_findings": ["Pattern recognized"]
            },
            "action_plan": {
                "action": "hold",
                "position_size_pct": 0.0
            },
            "risk_flags": ["MOCK_DATA"],
            "next_steps": ["Wait for real integration"]
        }
        return RawLLMResponse(
            ok=True,
            stdout=json.dumps(mock_json),
            stderr="",
            exit_code=0,
            duration_ms=10,
            timed_out=False
        )
