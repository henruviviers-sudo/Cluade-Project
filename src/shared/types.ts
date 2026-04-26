export type Exchange = "luno" | "valr" | "altcointrader";

export type Pair = string;

export interface Ticker {
  exchange: Exchange;
  pair: Pair;
  bid: number | null;
  ask: number | null;
  last: number | null;
  timestamp: number;
}

export interface ExchangeSnapshot {
  exchange: Exchange;
  ok: boolean;
  tickers: Ticker[];
  error?: string;
  fetchedAt: number;
  latencyMs: number;
}

export interface Snapshot {
  generatedAt: number;
  exchanges: ExchangeSnapshot[];
}

export const TRACKED_PAIRS = ["BTCZAR", "ETHZAR", "SOLZAR", "XRPZAR"] as const;
export type TrackedPair = (typeof TRACKED_PAIRS)[number];
