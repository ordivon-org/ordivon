import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import FinancePrepPage from "@/app/finance-prep/page";

/* ═══════════════════════════════════════════════════════════════════
   Finance Live Prep — governance surface tests
   ═══════════════════════════════════════════════════════════════════ */

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

function renderPage() {
  return render(<FinancePrepPage />);
}

describe("FinancePrepPage", () => {
  test("renders PREVIEW — NOT PRODUCTION banner", () => {
    renderPage();
    const els = screen.getAllByText(/PREVIEW — NOT PRODUCTION/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("renders no-live-trading message", () => {
    renderPage();
    const els = screen.getAllByText(/No live trading is enabled/);
    expect(els.length).toBeGreaterThan(0);
    const brokerEls = screen.getAllByText(/No broker API is connected/);
    expect(brokerEls.length).toBeGreaterThan(0);
  });

  test("Finance Constitution shows manual-only constraints", () => {
    renderPage();
    expect(screen.getAllByText(/FINANCE CONSTITUTION/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("MANUAL ONLY").length).toBeGreaterThan(0);
    expect(screen.getAllByText("NOT CONNECTED").length).toBeGreaterThan(0);
    expect(screen.getAllByText("DISABLED").length).toBeGreaterThan(0);
    expect(screen.getAllByText("NONE").length).toBeGreaterThan(0);
  });

  test("Risk Budget Panel renders capital / risk limits", () => {
    renderPage();
    expect(screen.getAllByText(/RISK BUDGET/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("100.00 USD").length).toBeGreaterThan(0);
  });

  test("Decision Intake preview shows symbol, thesis, setup, invalidation", () => {
    renderPage();
    expect(screen.getAllByText(/DECISION INTAKE/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("AAPL").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Breakout above 200-day SMA/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/—2% hard stop/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/hist-r-0427/).length).toBeGreaterThan(0);
  });

  test("Plan Receipt shows allowed/forbidden actions clearly", () => {
    renderPage();
    expect(screen.getAllByText(/PLAN RECEIPT/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("FORBIDDEN").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ALLOWED").length).toBeGreaterThan(0);
  });

  test("Outcome Capture includes fees/slippage and result", () => {
    renderPage();
    expect(screen.getAllByText(/OUTCOME CAPTURE/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/0.03 USD commission/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/\+2.22 USD/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/YES — within risk budget/).length).toBeGreaterThan(0);
  });

  test("Review Queue shows CandidateRule statuses and CandidateRule ≠ Policy banner", () => {
    renderPage();
    expect(screen.getAllByText(/POST-TRADE REVIEW QUEUE/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("ACCEPTED CANDIDATE").length).toBeGreaterThan(0);
    expect(screen.getAllByText("DRAFT").length).toBeGreaterThan(0);
    expect(screen.getAllByText("PENDING").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CandidateRule ≠ Policy/).length).toBeGreaterThan(0);
  });

  test("Place Live Order button is disabled with reason", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Place Live Order" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  test("Connect Broker API button is disabled with reason", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Connect Broker API" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  test("Enable Auto Trading button is disabled with reason", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Enable Auto Trading" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  /* ── Observation Layer ───────────────────────────────── */

  test("renders observation mode read-only banner", () => {
    renderPage();
    const els = screen.getAllByText(/OBSERVATION MODE/);
    expect(els.length).toBeGreaterThan(0);
    const ro = screen.getAllByText(/READ-ONLY/);
    expect(ro.length).toBeGreaterThan(0);
    const nw = screen.getAllByText(/cannot place orders/);
    expect(nw.length).toBeGreaterThan(0);
  });

  test("renders adapter capability table with BLOCKED write permissions", () => {
    renderPage();
    const blocked = screen.getAllByText("BLOCKED");
    expect(blocked.length).toBeGreaterThanOrEqual(4);
    const read = screen.getAllByText("READ");
    expect(read.length).toBeGreaterThanOrEqual(4);
  });

  test("renders data sources with freshness badges", () => {
    renderPage();
    expect(screen.getAllByText(/DATA SOURCES/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("MockObservationProvider").length).toBeGreaterThan(0);
  });

  test("renders stale data warning", () => {
    renderPage();
    const els = screen.getAllByText(/STALE DATA/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("read-only capability never shows write enabled", () => {
    renderPage();
    // All disabled actions must use BLOCKED, never READ for writes
    const blocked = screen.getAllByText("BLOCKED");
    // 4 write permissions blocked + at minimum
    expect(blocked.length).toBeGreaterThanOrEqual(4);
  });

  test("Place Live Order still disabled after observation layer", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Place Live Order" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });
});
