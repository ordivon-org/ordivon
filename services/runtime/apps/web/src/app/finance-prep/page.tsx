"use client";

import { useEffect, useState } from "react";

import { getApiBaseUrl } from "@/lib/api";
import {
  FinanceLivePrepBanner,
  FinanceConstitutionSummary,
  RiskBudgetPanel,
  DecisionIntakePreview,
  PlanReceiptPreview,
  OutcomeCapturePreview,
  PostTradeReviewQueuePreview,
  CandidateRuleIsNotPolicyBanner,
  DisabledHighRiskAction,
  GovernanceStyles,
  ObservationModeBanner,
  AdapterCapabilityTable,
  ObservationSourcePanel,
  StaleDataWarning,
  ProviderStatusBanner,
} from "@/components/governance";

/* ── Health response type ─────────────────────────────────── */

type HealthStatus = {
  provider_id: string;
  environment: string;
  status: string;
  last_checked_at: string;
  freshness: string;
  account_alias: string;
  total_equity: number | null;
  available_cash: number | null;
  sample_symbol: string;
  sample_price: number | null;
  write_capabilities: string[];
  error_summary: string;
};

/* ── Constitution ─────────────────────────────────────────── */

const CONSTITUTION = [
  { rule: "Capital", value: "100 USD (placeholder)" },
  { rule: "Execution", value: "MANUAL ONLY" },
  { rule: "Leverage", value: "NONE" },
  { rule: "Margin", value: "NONE — CASH ACCOUNT ONLY" },
  { rule: "Derivatives", value: "NONE" },
  { rule: "Broker API", value: "ALPACA PAPER (READ-ONLY)" },
  { rule: "Auto Trading", value: "DISABLED" },
  { rule: "Intake Required", value: "MANDATORY BEFORE TRADE" },
  { rule: "Outcome Capture Required", value: "MANDATORY AFTER TRADE" },
  { rule: "Post-Trade Review", value: "MANDATORY" },
];

/* ── Risk Budget (sample) ─────────────────────────────────── */

const SAMPLE_BUDGET = {
  totalCapital: "100.00 USD",
  maxTotalLoss: "—50.00 USD (hard stop)",
  maxPerTradeRisk: "5.00 USD (5% of capital)",
  dailyStopPct: "—15% drawdown",
  streakStopLosses: "3 consecutive losses",
};

/* ── Decision Intake (sample) ─────────────────────────────── */

const SAMPLE_INTAKE = [
  { label: "Symbol", value: "AAPL" },
  { label: "Thesis", value: "Breakout above 200-day SMA on volume confirmation" },
  { label: "Setup", value: "Buy stop at 195.00; confirmation above 194.50" },
  { label: "Entry Plan", value: "1 share at limit 194.75 — 195.25" },
  { label: "Invalidation", value: "Closes below 193.00 / SMA break" },
  { label: "Stop Condition", value: "—2% hard stop at 190.59" },
  { label: "Max Risk", value: "4.16 USD (≤ 5% capital)" },
  { label: "Evidence Refs", value: "hist-r-0427, sma-c-0428" },
];

/* ── Plan Receipt (sample) ────────────────────────────────── */

const SAMPLE_RECEIPT = [
  { label: "Governance Decision", value: "INTAKE_ACCEPTED (manual only)", allowed: true },
  { label: "Allowed Action", value: "Manual market order", allowed: true },
  { label: "Forbidden Action", value: "Automated broker order / API", allowed: false },
  { label: "Exit Plan", value: "Trailing stop 1% below daily VWAP" },
  { label: "Rollback Plan", value: "Immediate market close if loss > 3 USD" },
  { label: "Evidence Refs", value: "intake-0429-001, risk-budget-v1" },
];

/* ── Outcome Capture (sample) ──────────────────────────────── */

const SAMPLE_OUTCOME = [
  { label: "Entry", value: "195.12 (filled at 10:32)" },
  { label: "Exit", value: "197.45 (trailing stop at 14:10)" },
  { label: "Fees / Slippage", value: "0.03 USD commission + 0.08 slippage" },
  { label: "Result", value: "+2.22 USD (gross +2.33)" },
  { label: "Rule Followed?", value: "YES — within risk budget" },
  { label: "Deviation?", value: "None" },
];

/* ── Review Queue (sample) ─────────────────────────────────── */

const SAMPLE_REVIEWS = [
  { status: "COMPLETED", trade: "TRD-001 AAPL", candidateLesson: "SMA breakout confirmed. Entry at 195.12 within plan.", crStatus: "accepted_candidate" as const },
  { status: "COMPLETED", trade: "TRD-002 MSFT", candidateLesson: "Reversal entry — thesis invalidated within 2 candles.", crStatus: "draft" as const },
  { status: "PENDING", trade: "TRD-003 NVDA", candidateLesson: "Gap open — waiting for review window.", crStatus: undefined },
];

/* ── Disabled actions ──────────────────────────────────────── */

const DISABLED = [
  {
    action: "Place Live Order",
    reason: "Live order execution is not enabled. This is a governance prep surface. Alpaca Paper Trading connection is read-only. See Phase 7 Finance Live Micro-Capital Dogfood.",
  },
  {
    action: "Connect Broker API",
    reason: "Broker API integration requires Phase 7 readiness review, separate credentials vault, and explicit governance approval.",
  },
  {
    action: "Enable Auto Trading",
    reason: "Automated trading is permanently disabled for micro-capital finance. All trading is MANUAL ONLY per Finance Constitution §4.",
  },
];

/* ── Adapter capability table ─────────────────────────────── */

const ADAPTER_CAPS = [
  { capability: "can_read_market_data", enabled: true },
  { capability: "can_read_account", enabled: true },
  { capability: "can_read_positions", enabled: true },
  { capability: "can_read_fills", enabled: true },
  { capability: "can_place_order", enabled: false },
  { capability: "can_cancel_order", enabled: false },
  { capability: "can_withdraw", enabled: false },
  { capability: "can_transfer", enabled: false },
];

/* ── Page ──────────────────────────────────────────────────── */

export default function FinancePrepPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function fetchHealth() {
      try {
        const base = getApiBaseUrl();
        const resp = await fetch(`${base}/health/finance-observation`, { cache: "no-store" });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data: HealthStatus = await resp.json();
        if (!cancelled) {
          setHealth(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Unknown error");
          setHealth(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchHealth();
    return () => { cancelled = true; };
  }, []);

  /* ── Derived observation display ──────────────────────── */

  const providerStatus: "connected" | "configured" | "degraded" | "unavailable" =
    !health ? "unavailable" :
    health.status === "connected" ? "connected" :
    health.status === "degraded" ? "degraded" :
    health.status === "unavailable" ? "unavailable" :
    "configured";

  const obsSources = health ? [
    { label: "Market Data", source: `Alpaca Paper (${health.environment})`, freshness: (health.freshness as "current" | "stale" | "degraded" | "missing"), lastUpdated: health.sample_symbol ? `${health.sample_symbol} @ ${health.sample_price}` : health.last_checked_at },
    { label: "Account", source: `Alpaca Paper (${health.environment})`, freshness: (health.freshness as "current" | "stale" | "degraded" | "missing"), lastUpdated: health.account_alias ? `Alias: ${health.account_alias} | Equity: $${health.total_equity?.toLocaleString() ?? "—"}` : health.last_checked_at },
    { label: "Positions", source: `Alpaca Paper (${health.environment})`, freshness: "degraded" as const, lastUpdated: health.last_checked_at },
    { label: "Fills", source: `Alpaca Paper (${health.environment})`, freshness: "stale" as const, lastUpdated: "No fills yet (paper account empty)" },
  ] : [
    { label: "Market Data", source: "Unavailable", freshness: "missing" as const, lastUpdated: "—" },
    { label: "Account", source: "Unavailable", freshness: "missing" as const, lastUpdated: "—" },
    { label: "Positions", source: "Unavailable", freshness: "missing" as const, lastUpdated: "—" },
    { label: "Fills", source: "Unavailable", freshness: "missing" as const, lastUpdated: "—" },
  ];

  const hasStale = health
    ? health.freshness !== "current"
    : true;

  /* ── Render ───────────────────────────────────────────── */

  return (
    <div style={{ padding: "2rem", maxWidth: "960px", margin: "0 auto" }}>
      <GovernanceStyles />
      <article className="ordivon-workbench" style={{ gap: "1.5rem" }}>
        <FinanceLivePrepBanner />

        {/* ── 0. Observation Layer ──────────────────────── */}

        <ObservationModeBanner />

        {loading && (
          <div className="ordivon-banner" style={{ background: "rgba(137,176,255,0.06)", borderColor: "var(--border-color)" }}>
            <strong>⏳ Loading observation health...</strong>
            <p>Connecting to Alpaca Paper health endpoint. This may take a moment.</p>
          </div>
        )}

        {error && !loading && (
          <div className="ordivon-banner" style={{ background: "var(--ordivon-banner-preview-bg)", borderColor: "var(--ordivon-banner-preview-border)" }}>
            <strong>⚠ HEALTH ENDPOINT UNREACHABLE</strong>
            <p>Could not reach /health/finance-observation: {error}. Displaying fallback data. Ensure the API server is running and Alpaca keys are configured.</p>
          </div>
        )}

        {!loading && (
          <ProviderStatusBanner status={providerStatus} adapterId={health?.provider_id ?? "alpaca-paper"} paperUrl="paper-api.alpaca.markets" />
        )}

        <section>
          <h2 style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 0.5rem" }}>
            0 — Observation Layer (Alpaca Paper, Read-Only)
          </h2>
          <ObservationSourcePanel sources={obsSources} />
          <div style={{ height: "0.5rem" }} />
          <StaleDataWarning hasStale={hasStale} />
          <div style={{ height: "0.5rem" }} />
          {health && (
            <div className="ordivon-banner" style={{ background: "rgba(50,180,220,0.04)", borderColor: "var(--ordivon-approval-shadow)", fontSize: "0.78rem", marginBottom: "0.75rem" }}>
              <strong>📋 Paper account only — not live trading</strong>
              <p>Environment: {health.environment}. Write capabilities: [{health.write_capabilities.join(", ") || "none"}]. This is a paper trading simulation. No real money is involved. No orders can be placed.</p>
            </div>
          )}
          <AdapterCapabilityTable rows={ADAPTER_CAPS} />
        </section>

        {/* ── 1. Constitution &amp; Risk Budget ────────── */}

        <section>
          <h2 style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 0.5rem" }}>
            1 — Constitution &amp; Risk Budget
          </h2>
          <FinanceConstitutionSummary rules={CONSTITUTION} />
          <div style={{ height: "0.75rem" }} />
          <RiskBudgetPanel budget={SAMPLE_BUDGET} />
        </section>

        <section>
          <h2 style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 0.5rem" }}>
            2 — Decision Intake &amp; Plan Receipt
          </h2>
          <DecisionIntakePreview rows={SAMPLE_INTAKE} />
          <div style={{ height: "0.75rem" }} />
          <PlanReceiptPreview rows={SAMPLE_RECEIPT} />
        </section>

        <section>
          <h2 style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 0.5rem" }}>
            3 — Outcome Capture &amp; Post-Trade Review
          </h2>
          <OutcomeCapturePreview rows={SAMPLE_OUTCOME} />
          <div style={{ height: "0.75rem" }} />
          <PostTradeReviewQueuePreview entries={SAMPLE_REVIEWS} />
          <div style={{ height: "0.5rem" }} />
          <CandidateRuleIsNotPolicyBanner />
        </section>

        <section>
          <h2 style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 0.5rem" }}>
            4 — Disabled High-Risk Actions
          </h2>
          <div className="ordivon-workbench" style={{ gap: "0.6rem" }}>
            {DISABLED.map((d, i) => (
              <DisabledHighRiskAction key={i} action={d.action} reason={d.reason} />
            ))}
          </div>
        </section>
      </article>
    </div>
  );
}
