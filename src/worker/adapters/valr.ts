import type { ExchangeSnapshot, Ticker } from "../../shared/types";

interface ValrMarketSummary {
  currencyPair: string;
  bidPrice: string;
  askPrice: string;
  lastTradedPrice: string;
  created: string;
}

export async function fetchValr(pairs: string[]): Promise<ExchangeSnapshot> {
  const started = Date.now();
  try {
    const res = await fetch("https://api.valr.com/v1/public/marketsummary", {
      headers: { accept: "application/json" },
    });
    if (!res.ok) throw new Error(`valr ${res.status}`);
    const body = (await res.json()) as ValrMarketSummary[];
    const wanted = new Set(pairs);
    const tickers: Ticker[] = body
      .filter((t) => wanted.has(t.currencyPair))
      .map((t) => ({
        exchange: "valr",
        pair: t.currencyPair,
        bid: toNum(t.bidPrice),
        ask: toNum(t.askPrice),
        last: toNum(t.lastTradedPrice),
        timestamp: Date.parse(t.created) || Date.now(),
      }));
    return {
      exchange: "valr",
      ok: true,
      tickers,
      fetchedAt: Date.now(),
      latencyMs: Date.now() - started,
    };
  } catch (err) {
    return {
      exchange: "valr",
      ok: false,
      tickers: [],
      error: (err as Error).message,
      fetchedAt: Date.now(),
      latencyMs: Date.now() - started,
    };
  }
}

function toNum(s: string | undefined): number | null {
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}
