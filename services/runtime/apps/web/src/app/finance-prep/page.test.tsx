import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import FinancePrepPage from "@/app/finance-prep/page";

/* ═══════════════════════════════════════════════════════════════════
   Finance Prep — Observation Integration tests (Phase 6J)
   ═══════════════════════════════════════════════════════════════════ */

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

function renderPage() {
  return render(<FinancePrepPage />);
}

describe("FinancePrepPage — Observation Integration", () => {
  /* ── Read-only mode ──────────────────────────────────── */

  test("renders OBSERVATION MODE — READ-ONLY banner", () => {
    renderPage();
    const els = screen.getAllByText(/OBSERVATION MODE/);
    expect(els.length).toBeGreaterThan(0);
    const ro = screen.getAllByText(/READ-ONLY/);
    expect(ro.length).toBeGreaterThan(0);
  });

  /* ── Provider status ─────────────────────────────────── */

  test("renders Alpaca Paper provider connected status", () => {
    renderPage();
    const els = screen.getAllByText(/PROVIDER CONNECTED/);
    expect(els.length).toBeGreaterThan(0);
    const alpaca = screen.getAllByText(/alpaca-paper/);
    expect(alpaca.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/paper-api.alpaca.markets/).length).toBeGreaterThan(0);
  });

  test("provider banner states no orders can be placed", () => {
    renderPage();
    const els = screen.getAllByText(/No orders can be placed/);
    expect(els.length).toBeGreaterThan(0);
    const ro = screen.getAllByText(/read-only/);
    expect(ro.length).toBeGreaterThan(0);
  });

  /* ── Observation sources labeled Alpaca Paper ─────────── */

  test("data sources show Alpaca Paper provider", () => {
    renderPage();
    const sources = screen.getAllByText("Alpaca Paper (alpaca-py)");
    expect(sources.length).toBeGreaterThanOrEqual(2);
  });

  test("account source shows paper account ID", () => {
    renderPage();
    const els = screen.getAllByText(/PA37AKH0E5AT/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("fills source shows paper account empty", () => {
    renderPage();
    const els = screen.getAllByText(/No fills yet/);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── Data freshness ───────────────────────────────────── */

  test("renders stale data warning", () => {
    renderPage();
    const els = screen.getAllByText(/STALE DATA/);
    expect(els.length).toBeGreaterThan(0);
  });

  test("shows after-hours market data note", () => {
    renderPage();
    const els = screen.getAllByText(/after-hours/);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── Adapter capability contract ──────────────────────── */

  test("adapter capability shows BLOCKED write permissions", () => {
    renderPage();
    const blocked = screen.getAllByText("BLOCKED");
    // 4 write capabilities + at minimum
    expect(blocked.length).toBeGreaterThanOrEqual(4);
    const read = screen.getAllByText("READ");
    expect(read.length).toBeGreaterThanOrEqual(4);
  });

  test("capability table includes alpaca-paper labels on read capabilities", () => {
    renderPage();
    const els = screen.getAllByText(/alpaca-paper/);
    expect(els.length).toBeGreaterThanOrEqual(5); // 4 capabilities + provider banner
  });

  /* ── High-risk actions disabled ───────────────────────── */

  test("Place Live Order remains disabled with Alpaca note", () => {
    renderPage();
    const btns = screen.getAllByRole("button", { name: "Place Live Order" });
    expect(btns.length).toBeGreaterThan(0);
    btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
    const reason = screen.getAllByText(/Alpaca Paper Trading/);
    expect(reason.length).toBeGreaterThan(0);
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

  /* ── Constitution updated ──────────────────────────────── */

  test("constitution shows Alpaca Paper as broker API", () => {
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
    expect(html).not.toMatch(/PKIGUNUW|7v2Uxq3|secret.?key|api.?secret/i);
  });

  /* ── Section labeling ──────────────────────────────────── */

  test("section 0 labeled with Alpaca Paper", () => {
    renderPage();
    const els = screen.getAllByText(/Observation Layer/);
    expect(els.length).toBeGreaterThan(0);
    const alpaca = screen.getAllByText(/Alpaca Paper/);
    expect(alpaca.length).toBeGreaterThan(0);
  });

  test("no action button implies Ordivon placed an order", () => {
    renderPage();
    // No button exists with "submit", "execute order", "place trade", "buy", "sell"
    const buttons = screen.queryAllByRole("button");
    const orderButtons = buttons.filter(b =>
      /\b(submit|execute.?order|place.?trade|buy|sell)\b/i.test(b.textContent || "")
    );
    expect(orderButtons.length).toBe(0);
  });
});
