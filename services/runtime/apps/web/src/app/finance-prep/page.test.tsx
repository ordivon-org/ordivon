import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import FinancePrepPage from "@/app/finance-prep/page";

/* ═══════════════════════════════════════════════════════════════════
   Finance Prep — Observation Integration tests (Phase 6J-S)
   ═══════════════════════════════════════════════════════════════════ */

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

function renderPage() {
  return render(<FinancePrepPage />);
}

describe("FinancePrepPage — Observation Integration", () => {
  /* ── Provider status: configured (not connected) ──────── */

  test("renders PAPER PROVIDER READY — not PROVIDER CONNECTED", () => {
    renderPage();
    const els = screen.getAllByText(/PAPER PROVIDER READY/);
    expect(els.length).toBeGreaterThan(0);
    // Must NOT claim live connection
    expect(screen.queryByText(/PROVIDER CONNECTED/)).toBeNull();
  });

  test("renders static preview data disclaimer", () => {
    renderPage();
    const els = screen.getAllByText(/This page uses static preview data/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("renders does not perform live account read notice", () => {
    renderPage();
    const els = screen.getAllByText(/does not perform a live Alpaca account read/);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── Account ID masked ────────────────────────────────── */

  test("account ID is masked in rendered output", () => {
    renderPage();
    const masked = screen.getAllByText(/PA37\*{4}E5AT/);
    expect(masked.length).toBeGreaterThan(0);
  });

  test("full account ID is not visible", () => {
    renderPage();
    expect(screen.queryByText("PA37AKH0E5AT")).toBeNull();
  });

  /* ── Read-only mode ──────────────────────────────────── */

  test("renders OBSERVATION MODE — READ-ONLY banner", () => {
    renderPage();
    const els = screen.getAllByText(/OBSERVATION MODE/);
    expect(els.length).toBeGreaterThan(0);
    const ro = screen.getAllByText(/READ-ONLY/);
    expect(ro.length).toBeGreaterThan(0);
  });

  /* ── Provider banner states no orders ─────────────────── */

  test("provider banner states no orders can be placed", () => {
    renderPage();
    const els = screen.getAllByText(/No orders can be placed/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("provider banner mentions alpaca-paper", () => {
    renderPage();
    const els = screen.getAllByText(/alpaca-paper/);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── Data sources ─────────────────────────────────────── */

  test("data sources show Alpaca Paper provider", () => {
    renderPage();
    const sources = screen.getAllByText("Alpaca Paper (alpaca-py)");
    expect(sources.length).toBeGreaterThanOrEqual(2);
  });

  /* ── Data freshness ───────────────────────────────────── */

  test("renders stale data warning", () => {
    renderPage();
    const els = screen.getAllByText(/STALE DATA/);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── Adapter capability contract ──────────────────────── */

  test("adapter capability shows BLOCKED write permissions", () => {
    renderPage();
    const blocked = screen.getAllByText("BLOCKED");
    expect(blocked.length).toBeGreaterThanOrEqual(4);
    const read = screen.getAllByText("READ");
    expect(read.length).toBeGreaterThanOrEqual(4);
  });

  /* ── High-risk actions disabled ───────────────────────── */

  test("Place Live Order remains disabled", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Place Live Order" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  test("Connect Broker API remains disabled", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Connect Broker API" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  test("Enable Auto Trading remains disabled", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Enable Auto Trading" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  /* ── Constitution ─────────────────────────────────────── */

  test("constitution shows Alpaca Paper as read-only broker", () => {
    renderPage();
    const els = screen.getAllByText("ALPACA PAPER (READ-ONLY)");
    expect(els.length).toBeGreaterThan(0);
  });

  test("constitution shows cash account only", () => {
    renderPage();
    const els = screen.getAllByText(/CASH ACCOUNT ONLY/);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── No secrets exposed ────────────────────────────────── */

  test("no secret-like values appear in rendered output", () => {
    renderPage();
    const html = document.body.innerHTML;
    expect(html).not.toMatch(/PKIGUNUW|7v2Uxq3/);
    expect(html).not.toMatch(/PA37AKH0/);
  });

  /* ── No order buttons ─────────────────────────────────── */

  test("no action button implies Ordivon placed an order", () => {
    renderPage();
    const buttons = screen.queryAllByRole("button");
    const orderButtons = buttons.filter(b =>
      /\b(submit|execute.?order|place.?trade|buy|sell)\b/i.test(b.textContent || "")
    );
    expect(orderButtons.length).toBe(0);
  });

  /* ── Preview labeling ──────────────────────────────────── */

  test("renders PREVIEW — NOT PRODUCTION banner", () => {
    renderPage();
    const els = screen.getAllByText(/PREVIEW — NOT PRODUCTION/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("renders No live trading is enabled message", () => {
    renderPage();
    const els = screen.getAllByText(/No live trading/);
    expect(els.length).toBeGreaterThan(0);
  });
});
