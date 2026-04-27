from __future__ import annotations

import time
from typing import Any

import httpx

from intelligence.runtime.errors import RuntimeExecutionError, RuntimeTaskError, RuntimeUnavailableError
from shared.config.settings import settings


class HermesRuntimeError(RuntimeExecutionError):
    pass


class HermesUnavailableError(RuntimeUnavailableError, HermesRuntimeError):
    pass


class HermesTaskError(RuntimeTaskError, HermesRuntimeError):
    pass


class HermesClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_token: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.hermes_base_url).rstrip("/")
        self.api_token = api_token or settings.hermes_api_token
        self.timeout_seconds = timeout_seconds or settings.hermes_timeout_seconds
        self.max_retries = max_retries if max_retries is not None else settings.hermes_max_retries
        self.retry_backoff_seconds = (
            retry_backoff_seconds if retry_backoff_seconds is not None else settings.hermes_retry_backoff_seconds
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _sleep_before_retry(self, attempt: int) -> None:
        if attempt <= 0 or self.retry_backoff_seconds <= 0:
            return
        time.sleep(self.retry_backoff_seconds * attempt)

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code >= 500 or status_code == 429

    def _extract_error_message(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text
        if isinstance(payload, dict):
            return str(payload.get("detail") or payload.get("error") or payload)
        return str(payload)

    def health_check(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(f"{self.base_url}/health", headers=self._headers())
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise HermesUnavailableError("Hermes health check timed out.", retryable=True) from exc
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_message(exc.response)
            raise HermesUnavailableError(
                f"Hermes health check failed ({exc.response.status_code}): {detail}",
                retryable=self._is_retryable_status(exc.response.status_code),
                status_code=exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            raise HermesUnavailableError("Hermes health check failed.", retryable=True) from exc

    def run_task(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "task_type": task_type,
            **payload,
        }
        last_error: RuntimeExecutionError | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(f"{self.base_url}/tasks", json=body, headers=self._headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status") not in {"completed", "success"}:
                    raise HermesTaskError(
                        data.get("error") or f"Hermes returned non-success for {task_type}",
                        task_type=task_type,
                    )
                return data
            except httpx.TimeoutException as exc:
                last_error = HermesUnavailableError(
                    f"Hermes task timed out: {task_type}",
                    task_type=task_type,
                    retryable=True,
                )
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt + 1)
                    continue
                raise last_error from exc
            except httpx.HTTPStatusError as exc:
                detail = self._extract_error_message(exc.response)
                retryable = self._is_retryable_status(exc.response.status_code)
                last_error = HermesTaskError(
                    f"Hermes task failed ({exc.response.status_code}) for {task_type}: {detail}",
                    task_type=task_type,
                    retryable=retryable,
                    status_code=exc.response.status_code,
                )
                if retryable and attempt < self.max_retries:
                    self._sleep_before_retry(attempt + 1)
                    continue
                raise last_error from exc
            except httpx.HTTPError as exc:
                last_error = HermesUnavailableError(
                    f"Hermes task unavailable: {task_type}",
                    task_type=task_type,
                    retryable=True,
                )
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt + 1)
                    continue
                raise last_error from exc

        if last_error is not None:
            raise last_error
        raise HermesUnavailableError(f"Hermes task failed without a captured error: {task_type}", task_type=task_type)
