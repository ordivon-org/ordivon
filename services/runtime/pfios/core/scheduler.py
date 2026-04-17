"""
pfios.core.scheduler — PFIOS Background Task Scheduler
负责驱动数据同步任务和定期分析任务。
"""
from __future__ import annotations

import asyncio
import logging
import signal
import time
from datetime import datetime
from typing import Any, Callable, Coroutine

from pfios.core.config.settings import settings
from pfios.skills.ingestion.jobs.sync_market_ohlcv import sync_market_ohlcv
from pfios.skills.ingestion.jobs.sync_account import sync_account

logger = logging.getLogger(__name__)

class PFIOSScheduler:
    """
    PFIOS 核心调度器 (Heartbeat)
    运行在后台，负责：
    1. 市场 OHLCV 同步 (每 15-60 分钟)
    2. 账户持仓与余额同步 (每 1-5 分钟)
    3. 自定义 Hook 支持
    """
    def __init__(self):
        self.running = False
        self._tasks: list[asyncio.Task] = []
        self.exchange_config = {
            "exchange": "okx",
            "symbols": settings.symbols,
            "timeframes": settings.timeframes,
            "timeout_ms": 30000,
            # 从 settings 中读取凭证
            "apiKey": settings.okx_api_key,
            "secret": settings.okx_secret,
            "password": settings.okx_passphrase,
        }

    async def _run_periodic(self, name: str, interval_seconds: int, func: Callable[..., Any], *args, **kwargs):
        """通用周期任务执行器"""
        logger.info(f"[Scheduler] Starting periodic task: {name} (every {interval_seconds}s)")
        while self.running:
            try:
                start_time = time.time()
                logger.info(f"[Scheduler] Executing {name}...")
                
                # 兼容同步和异步方法
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # 在线程池中跑同步阻塞任务，避免卡死 event loop
                    result = await asyncio.to_thread(func, *args, **kwargs)
                
                duration = time.time() - start_time
                logger.info(f"[Scheduler] Finished {name} in {duration:.2f}s. Result: {result}")
            except Exception as e:
                logger.error(f"[Scheduler] Task {name} failed: {e}", exc_info=True)
            
            await asyncio.sleep(interval_seconds)

    async def start(self):
        """启动调度器"""
        if self.running:
            return
        self.running = True
        logger.info("[Scheduler] PFIOS Heartbeat started.")

        # 1. 账户同步：频率较高，默认 120 秒
        self._tasks.append(asyncio.create_task(
            self._run_periodic("sync_account", 120, sync_account, self.exchange_config)
        ))

        # 2. 市场 OHLCV 同步：频率中等，默认 900 秒 (15分钟)
        self._tasks.append(asyncio.create_task(
            self._run_periodic("sync_market_ohlcv", 900, sync_market_ohlcv, self.exchange_config)
        ))

        # 3. 结果监测 (Outcome Detection): 每 15 分钟运行一次
        from pfios.orchestrator.outcome_detector import OutcomeDetector
        detector = OutcomeDetector()
        self._tasks.append(asyncio.create_task(
            self._run_periodic("outcome_detection", 900, detector.run_detection_cycle)
        ))

        # 4. 复盘生成 (Review Generation): 每小时运行一次
        from pfios.orchestrator.review_generator import ReviewGenerator
        generator = ReviewGenerator()
        self._tasks.append(asyncio.create_task(
            self._run_periodic("review_generation", 3600, generator.run_generation_cycle)
        ))

        # 5. 使用详情与指标同步 (Stability/Usage): 每天运行一次
        # from pfios.skills.stability.jobs.sync_usage import sync_daily_usage
        # self._tasks.append(asyncio.create_task(
        #     self._run_periodic("sync_usage", 86400, sync_daily_usage)
        # ))

    async def stop(self):
        """优雅停止"""
        logger.info("[Scheduler] Stopping PFIOS Heartbeat...")
        self.running = False
        for task in self._tasks:
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        logger.info("[Scheduler] PFIOS Heartbeat stopped.")

async def main():
    """生产环境下运行调度器的入口"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    scheduler = PFIOSScheduler()
    
    # 注册信号处理，支持 Ctrl+C 优雅退出
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(scheduler.stop()))

    try:
        await scheduler.start()
        # 持续运行直到停止
        while scheduler.running:
            await asyncio.sleep(1)
    except Exception as e:
        logger.critical(f"[Scheduler] Critical crash: {e}")
    finally:
        await scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
