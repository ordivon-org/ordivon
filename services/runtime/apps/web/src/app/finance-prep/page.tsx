"use client";

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
} from "@/components/governance";

/* ── Observation Layer (sample) ───────────────────────────── */

const OBS_SOURCES = [
  { label: "Market Data", source: "MockObservationProvider", freshness: "stale" as const, lastUpdated: "2026-04-29 08:30 UTC" },
  { label: "Account", source: "MockObservationProvider", freshness: "stale" as const, lastUpdated: "2026-04-29 08:30 UTC" },
  { label: "Positions", source: "MockObservationProvider", freshness: "stale" as const, lastUpdated: "2026-04-29 08:30 UTC" },
  { label: "Fills", source: "Manual Entry", freshness: "current" as const, lastUpdated: "2026-04-29 09:00 UTC" },
];

const ADAPTER_CAPABILITIES = [
  { capability: "can_read_market_data", enabled: true },
  { capability: "can_read_account", enabled: true },
  { capability: "can_read_positions", enabled: true },
  { capability: "can_read_fills", enabled: true },
  { capability: "can_place_order", enabled: false },
  { capability: "can_cancel_order", enabled: false },
  { capability: "can_withdraw", enabled: false },
  { capability: "can_transfer", enabled: false },
];

/* ── Constitution ─────────────────────────────────────────── */

const CONSTITUTION = [
  { rule: "Capital", value: "100 USD (placeholder)" },
  { rule: "Execution", value: "MANUAL ONLY" },
  { rule: "Leverage", value: "NONE" },
  { rule: "Margin", value: "NONE" },
  { rule: "Derivatives", value: "NONE" },
  { rule: "Broker API", value: "NOT CONNECTED" },
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
    reason: "Live order execution is not enabled. This is a governance prep surface. Broker API is not connected. See Phase 7 Finance Live Micro-Capital Dogfood.",
  },
  {
    action: "Connect Broker API",
    reason: "Broker API integration requires Phase 7 readiness review, separate credentials vault, and explicit governance approval. Not available in preview.",
  },
  {
    action: "Enable Auto Trading",
    reason: "Automated trading is permanently disabled for micro-capital finance. All trading is MANUAL ONLY per Finance Constitution §4.",
  },
];

/* ── Page ──────────────────────────────────────────────────── */

export default function FinancePrepPage() {
  return (
    <div style={{ padding: "2rem", maxWidth: "960px", margin: "0 auto" }}>
      <GovernanceStyles />
      <article className="ordivon-workbench" style={{ gap: "1.5rem" }}>
        <FinanceLivePrepBanner />

        {/* ── 0. Observation Layer ──────────────────────── */}

        <ObservationModeBanner />

        <section>
          <h2 style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: "0 0 0.5rem" }}>
            0 — Observation Layer
          </h2>
          <ObservationSourcePanel sources={OBS_SOURCES} />
          <div style={{ height: "0.5rem" }} />
          <StaleDataWarning hasStale={true} />
          <div style={{ height: "0.75rem" }} />
          <AdapterCapabilityTable rows={ADAPTER_CAPABILITIES} />
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
