import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 获取项目根目录 (financial-ai-os/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

class Settings(BaseSettings):
    """PFIOS 全局配置锚点 (Core Config V1.1)"""
    
    # 1. 环境层
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = True
    
    # 2. 存储锚点 (Paths)
    db_path: str = Field(default="db/pfios_main.duckdb", alias="DB_PATH")
    wiki_root: str = Field(default="wiki/obsidian", alias="WIKI_PATH")
    reports_root: str = Field(default="data/exports", alias="REPORTS_ROOT")
    audit_log_root: str = Field(default="data/logs/audit", alias="AUDIT_LOG_ROOT")
    
    # 3. 治理层规则锚点
    constitution_path: str = Field(default="policies/constitution.md", alias="CONSTITUTION_PATH")
    trading_limits_path: str = Field(default="policies/trading_limits.yaml", alias="TRADING_LIMITS_PATH")
    
    # 4. 模型锚点
    hermes_model: str = Field(default="openai/gpt-4o", alias="HERMES_MODEL")
    
    # 5. 迁移兼容性锚点 (Legacy Support)
    # 用于 Phase 2 指向旧仓库以方便读取旧配置或对比
    old_repo_root: str = Field(default="../quant-agent", alias="OLD_REPO_ROOT")

    # 6. 推理引擎 (Reasoning Layer) 配置 (Step 8.2 加入)
    reasoning_provider: str = Field(default="mock", alias="REASONING_PROVIDER")  # mock | hermes_cli
    hermes_runtime_path: str = Field(default="../hermes-runtime", alias="HERMES_RUNTIME_PATH")
    hermes_python_path: Optional[str] = Field(default=None, alias="HERMES_PYTHON_PATH")  # 显式 Python 解释器路径
    hermes_timeout_seconds: int = Field(default=60, alias="HERMES_TIMEOUT_SECONDS")
    reasoning_debug: bool = Field(default=False, alias="REASONING_DEBUG")
    reasoning_prompt_template: str = Field(default="base_analysis.j2", alias="REASONING_PROMPT_TEMPLATE")

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        extra="ignore"
    )

    # 路径解析助手 (确保所有模块拿到的都是绝对路径)
    def get_abs_path(self, relative_path: str) -> Path:
        p = Path(relative_path)
        return p if p.is_absolute() else ROOT_DIR / p

    @property
    def db_abs_path(self) -> Path:
        return self.get_abs_path(self.db_path)

    @property
    def wiki_abs_root(self) -> Path:
        return self.get_abs_path(self.wiki_root)

    @property
    def constitution_abs_path(self) -> Path:
        return self.get_abs_path(self.constitution_path)

    @property
    def trading_limits_abs_path(self) -> Path:
        return self.get_abs_path(self.trading_limits_path)

    @property
    def hermes_runtime_abs_path(self) -> Path:
        return self.get_abs_path(self.hermes_runtime_path)

    def get_hermes_python_executable(self) -> str:
        """获取真实的 Hermes 执行程序路径 (按约束 3 实现)"""
        if self.hermes_python_path:
            return self.hermes_python_path
        
        # 默认尝试从 runtime 路径推导 venv 路径 (Windows 惯例)
        venv_python = self.hermes_runtime_abs_path / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        
        return "python"  # 回退到全局 python

settings = Settings()
