import type { ExchangeSnapshot, Ticker } from "../../shared/types";

const LUNO_PAIRS: Record<string, string> = {
  BTCZAR: "XBTZAR",
  ETHZAR: "ETHZAR",
  SOLZAR: "SOLZAR",
  XRPZAR: "XRPZAR",
};

interface LunoTicker {
  pair: string;
  bid: string;
  ask: string;
  last_trade: string;
  timestamp: number;
}

interface LunoTickersResponse {
  tickers: LunoTicker[];
}

export async function fetchLuno(pairs: string[]): Promise<ExchangeSnapshot> {
  const started = Date.now();
  try {
    const res = await fetch("https://api.luno.com/api/1/tickers", {
      headers: { accept: "application/json" },
    });
    if (!res.ok) throw new Error(`luno ${res.status}`);
    const body = (await res.json()) as LunoTickersResponse;
    const wanted = new Set(pairs.map((p) => LUNO_PAIRS[p]).filter(Boolean));
    const tickers: Ticker[] = body.tickers
      .filter((t) => wanted.has(t.pair))
      .map((t) => ({
        exchange: "luno",
        pair: invert(LUNO_PAIRS, t.pair) ?? t.pair,
        bid: toNum(t.bid),
        ask: toNum(t.ask),
        last: toNum(t.last_trade),
        timestamp: t.timestamp,
      }));
    return {
      exchange: "luno",
      ok: true,
      tickers,
      fetchedAt: Date.now(),
      latencyMs: Date.now() - started,
    };
  } catch (err) {
    return {
      exchange: "luno",
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

function invert(map: Record<string, string>, value: string): string | null {
  for (const [k, v] of Object.entries(map)) if (v === value) return k;
  return null;
}
