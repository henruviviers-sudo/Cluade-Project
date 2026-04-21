# SA Crypto Tracker

Observed ZAR prices across local exchanges (Luno, VALR, AltCoinTrader).
Weekend 1 skeleton from the blueprint — deployable to Cloudflare Pages + Workers.

## Stack

- Vite + React 18 + TypeScript + Tailwind (frontend, built to `dist/`)
- Cloudflare Worker (`src/worker/index.ts`) exposing `/api/snapshot`
- No database, no auth, no user accounts. State lives in `localStorage` only.

## Layout

```
src/
  shared/types.ts          # Snapshot, Ticker, TRACKED_PAIRS
  worker/
    index.ts               # /api/snapshot, /api/health
    adapters/{luno,valr,altcointrader}.ts
  app/
    App.tsx, main.tsx, index.html, styles.css
    hooks/useSnapshot.ts   # 15s polling + stale-while-error
    components/PriceGrid.tsx
    lib/format.ts
```

## Dev

```
npm install
npm run dev:worker     # worker on :8787
npm run dev            # vite on :5173, proxies /api -> :8787
```

## Verify before ship

- [ ] Hit `http://127.0.0.1:8787/api/snapshot` — all three adapters return `ok: true`.
- [ ] AltCoinTrader endpoint shape: confirm `/v3/live` payload matches
      `src/worker/adapters/altcointrader.ts`. If not, adjust mapping or
      ship with Luno + VALR only and defer AltCoin to a point release.
- [ ] Copy audit (blueprint §7.4): no "BUY", "SELL", "HIGH CONVICTION" phrasing.

## Deploy

```
npm run build
npx wrangler pages deploy dist    # static site
npm run deploy                    # worker
```

Create a KV namespace and uncomment the `SNAPSHOT_CACHE` binding in `wrangler.toml`
before deploying if you want server-side caching (saves exchange-side rate limit).
