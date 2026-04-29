import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, test, vi, beforeEach, afterEach } from "vitest";
import FinancePrepPage from "@/app/finance-prep/page";

/* ═══════════════════════════════════════════════════════════════════
   Finance Prep — Health Integration tests (Phase 6L)
   ═══════════════════════════════════════════════════════════════════ */

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

/* ── Mock helpers ───────────────────────────────────────── */

const MOCK_CONNECTED = {
  provider_id: "alpaca-paper",
  environment: "paper",
  status: "connected",
  last_checked_at: "2026-04-29T10:00:00Z",
  freshness: "current",
  account_alias: "PA37****E5AT",
  total_equity: 100000,
  available_cash: 100000,
  sample_symbol: "AAPL",
  sample_price: 255.77,
  write_capabilities: [],
  error_summary: "",
};

const MOCK_DEGRADED = {
  ...MOCK_CONNECTED,
  status: "degraded",
  freshness: "degraded",
  error_summary: "Market data API timeout",
};

const MOCK_UNAVAILABLE = {
  ...MOCK_CONNECTED,
  status: "unavailable",
  freshness: "missing",
  account_alias: "",
  total_equity: null,
  available_cash: null,
  sample_symbol: "",
  sample_price: null,
  error_summary: "API keys not configured",
};

function mockFetch(response: object | null, ok = true, status = 200) {
  (global as any).fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => response,
  });
}

function mockFetchError() {
  (global as any).fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));
}

function renderPage() {
  return render(<FinancePrepPage />);
}

beforeEach(() => {
  mockFetch(MOCK_CONNECTED);
});

afterEach(() => {
  vi.restoreAllMocks();
});

/* ══════════════════════════════════════════════════════════════════ */

describe("FinancePrepPage — Health Integration", () => {
  /* ── Connected state ────────────────────────────────── */

  test("renders ALPACA PAPER READ-ONLY HEALTH after fetch", async () => {
    renderPage();
    await waitFor(() => {
      const els = screen.getAllByText(/alpaca-paper/i);
      expect(els.length).toBeGreaterThan(0);
    });
  });

  test("shows paper account only label when connected", async () => {
    mockFetch(MOCK_CONNECTED);
    renderPage();
    await waitFor(() => {
      const els = screen.getAllByText(/Paper account only/i);
      expect(els.length).toBeGreaterThan(0);
    });
  });

  test("shows empty write capabilities", async () => {
    renderPage();
    await waitFor(() => {
      // Adapter capability table should have BLOCKED entries
      const blocked = screen.getAllByText("BLOCKED");
      expect(blocked.length).toBeGreaterThanOrEqual(4);
    });
  });

  test("shows environment as paper", async () => {
    renderPage();
    await waitFor(() => {
      // Section 0 labels include 'paper', 'Alpaca Paper'
      const paperLabels = screen.getAllByText(/paper/i);
      expect(paperLabels.length).toBeGreaterThan(0);
    });
  });

  /* ── Degraded state ─────────────────────────────────── */

  test("shows degraded state with stale warning", async () => {
    mockFetch(MOCK_DEGRADED);
    renderPage();
    await waitFor(() => {
      const stale = screen.getAllByText(/STALE DATA/i);
      expect(stale.length).toBeGreaterThan(0);
    });
  });

  /* ── Unavailable fallback ───────────────────────────── */

  test("falls back to unavailable when endpoint returns unavailable", async () => {
    mockFetch(MOCK_UNAVAILABLE);
    renderPage();
    await waitFor(() => {
      const unavailable = screen.getAllByText(/PROVIDER UNAVAILABLE/i);
      expect(unavailable.length).toBeGreaterThan(0);
    });
  });

  /* ── Error state ────────────────────────────────────── */

  test("shows error banner when fetch fails", async () => {
    mockFetchError();
    renderPage();
    await waitFor(() => {
      const err = screen.getAllByText(/HEALTH ENDPOINT UNREACHABLE/i);
      expect(err.length).toBeGreaterThan(0);
    });
  });

  test("page does not crash on fetch failure", async () => {
    mockFetchError();
    renderPage();
    await waitFor(() => {
      // Still renders disabled actions
      const btns = screen.getAllByRole("button", { name: "Place Live Order" });
      expect(btns.length).toBeGreaterThan(0);
    });
  });

  /* ── Loading state ──────────────────────────────────── */

  test("shows loading state initially", () => {
    // Don't resolve fetch — it stays pending
    (global as any).fetch = vi.fn(() => new Promise(() => {}));
    renderPage();
    const els = screen.getAllByText(/Loading observation health/i);
    expect(els.length).toBeGreaterThan(0);
  });

  /* ── Redaction ─────────────────────────────────────── */

  test("rendered output has no raw account IDs", async () => {
    renderPage();
    await waitFor(() => {
      expect(document.body.innerHTML).not.toMatch(/PA37AKH0/);
    });
  });

  test("rendered output has no secret-like values", async () => {
    renderPage();
    await waitFor(() => {
      const html = document.body.innerHTML.toLowerCase();
      // Env var names in error messages are OK — but actual secrets are not
      expect(html).not.toMatch(/PKIGUNUW|7v2Uxq3/);
      expect(html).not.toMatch(/pk[0-9a-f]{20,}/i);
    });
  });

  /* ── High-risk actions ──────────────────────────────── */

  test("Place Live Order disabled on connected health", async () => {
    renderPage();
    await waitFor(() => {
      const btns = screen.getAllByRole("button", { name: "Place Live Order" });
      expect(btns.length).toBeGreaterThan(0);
      btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
    });
  });

  test("Connect Broker API disabled", async () => {
    renderPage();
    await waitFor(() => {
      const btns = screen.getAllByRole("button", { name: "Connect Broker API" });
      btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
    });
  });

  test("Enable Auto Trading disabled", async () => {
    renderPage();
    await waitFor(() => {
      const btns = screen.getAllByRole("button", { name: "Enable Auto Trading" });
      btns.forEach(btn => expect((btn as HTMLButtonElement).disabled).toBe(true));
    });
  });

  /* ── No order buttons ──────────────────────────────── */

  test("no order-related buttons exist", async () => {
    renderPage();
    await waitFor(() => {
      const buttons = screen.queryAllByRole("button");
      const orderButtons = buttons.filter(b =>
        /\b(submit|execute.?order|place.?trade|buy|sell)\b/i.test(b.textContent || "")
      );
      expect(orderButtons.length).toBe(0);
    });
  });

  /* ── Preview labels persist ────────────────────────── */

  test("PREVIEW — NOT PRODUCTION banner still renders", async () => {
    renderPage();
    await waitFor(() => {
      const els = screen.getAllByText(/PREVIEW — NOT PRODUCTION/);
      expect(els.length).toBeGreaterThan(0);
    });
  });

  test("No live trading message still renders", async () => {
    renderPage();
    await waitFor(() => {
      const els = screen.getAllByText(/No live trading/);
      expect(els.length).toBeGreaterThan(0);
    });
  });

  /* ── OBSERVATION MODE banner ───────────────────────── */

  test("OBSERVATION MODE — READ-ONLY banner renders", async () => {
    renderPage();
    await waitFor(() => {
      const els = screen.getAllByText(/OBSERVATION MODE/);
      expect(els.length).toBeGreaterThan(0);
    });
  });
});
