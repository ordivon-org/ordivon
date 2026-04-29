"""Health endpoints — API liveness + Finance observation health."""

from fastapi import APIRouter

from adapters.finance.health import get_alpaca_health_snapshot
from apps.api.app.schemas.health import FinanceObservationHealthResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="pfios-api")


@router.get("/health/finance-observation", response_model=FinanceObservationHealthResponse)
def finance_observation_health() -> FinanceObservationHealthResponse:
    """Read-only health check for Alpaca Paper observation provider.

    Returns redacted status only. No secrets, no full account IDs, no write capability.
    Performs GET requests to Alpaca Paper only.
    """
    snapshot = get_alpaca_health_snapshot()
    return FinanceObservationHealthResponse(
        provider_id=snapshot.provider_id,
        environment=snapshot.environment,
        status=snapshot.status,
        last_checked_at=snapshot.last_checked_at,
        freshness=snapshot.freshness,
        account_alias=snapshot.account_alias,
        total_equity=snapshot.total_equity,
        available_cash=snapshot.available_cash,
        sample_symbol=snapshot.sample_symbol,
        sample_price=snapshot.sample_price,
        write_capabilities=snapshot.write_capabilities,
        error_summary=snapshot.error_summary,
    )
