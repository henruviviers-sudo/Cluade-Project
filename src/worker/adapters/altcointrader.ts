import type { ExchangeSnapshot, Ticker } from "../../shared/types";

// AltCoinTrader's public docs are thin. The live ticker endpoint below
// returns per-coin quotes in ZAR. If the contract shifts, this adapter
// degrades gracefully (ok: false) rather than taking down the snapshot.
//
// Verification task before Weekend 1 ship: confirm this endpoint and
// payload shape against live traffic; adjust mapping as needed.
const ENDPOINT = "https://api.altcointrader.co.za/v3/live";

const ACT_SYMBOLS: Record<string, string> = {
  BTCZAR: "BTC",
  ETHZAR: "ETH",
  SOLZAR: "SOL",
  XRPZAR: "XRP",
};

interface ActQuote {
  Price?: string | number;
  Bid?: string | number;
  Ask?: string | number;
  Last?: string | number;
}

export async function fetchAltCoinTrader(
  pairs: string[],
): Promise<ExchangeSnapshot> {
  const started = Date.now();
  try {
    const res = await fetch(ENDPOINT, {
      headers: { accept: "application/json" },
    });
    if (!res.ok) throw new Error(`altcointrader ${res.status}`);
    const body = (await res.json()) as Record<string, ActQuote>;

    const tickers: Ticker[] = [];
    for (const pair of pairs) {
      const sym = ACT_SYMBOLS[pair];
      if (!sym) continue;
      const quote = body[sym];
      if (!quote) continue;
      tickers.push({
        exchange: "altcointrader",
        pair,
        bid: toNum(quote.Bid),
        ask: toNum(quote.Ask),
        last: toNum(quote.Last ?? quote.Price),
        timestamp: Date.now(),
      });
    }

    return {
      exchange: "altcointrader",
      ok: true,
      tickers,
      fetchedAt: Date.now(),
      latencyMs: Date.now() - started,
    };
  } catch (err) {
    return {
      exchange: "altcointrader",
      ok: false,
      tickers: [],
      error: (err as Error).message,
      fetchedAt: Date.now(),
      latencyMs: Date.now() - started,
    };
  }
}

function toNum(s: string | number | undefined): number | null {
  if (s === undefined || s === null) return null;
  const n = typeof s === "number" ? s : Number(s);
  return Number.isFinite(n) ? n : null;
}
