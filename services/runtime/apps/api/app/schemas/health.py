from __future__ import annotations


from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class FinanceObservationHealthResponse(BaseModel):
    """Redacted health status for Alpaca Paper observation provider.

    Safe to serialize. No secrets, no raw account IDs.
    """

    provider_id: str = "alpaca-paper"
    environment: str = "paper"
    status: str = "unavailable"
    last_checked_at: str = ""
    freshness: str = "missing"
    account_alias: str = ""
    total_equity: float | None = None
    available_cash: float | None = None
    sample_symbol: str = ""
    sample_price: float | None = None
    write_capabilities: list[str] = []
    error_summary: str = ""
