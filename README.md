# SA Crypto Tracker

Observed ZAR prices across local exchanges (Luno, VALR, AltCoinTrader).
Weekend 1 skeleton from the blueprint — deployable to Cloudflare Pages + Workers.

## Stack

- Vite + React 18 + TypeScript + Tailwind (frontend, built to `dist/`)
- Cloudflare Worker (`src/worker/index.ts`) exposing `/api/snapshot`
- No database, no auth, no user accounts. State lives in `localStorage` only.
- Installable PWA: manifest + service worker (offline shell + last-snapshot cache).
  Works on iOS (Safari → Share → Add to Home Screen) and Android (Chrome install prompt).

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

## Native (iOS + Android via Capacitor)

The same React bundle ships as a real app binary. Inside the native shell the
web bundle is served from `capacitor://localhost`, so API calls need an
absolute Worker URL — set it at build time:

```
# .env.production or your CI env
VITE_API_BASE=https://api.yourdomain.com
```

### First-time setup

One-off on each platform. Requires Xcode (iOS, macOS-only) and/or Android
Studio + JDK 17:

```
npm install
npx cap add ios
npx cap add android
```

This generates the `ios/` and `android/` folders — commit them.

### Build + open

```
npm run mobile:ios       # build web, sync, open Xcode
npm run mobile:android   # build web, sync, open Android Studio
```

Or run on a connected device / simulator:

```
npm run mobile:run:ios
npm run mobile:run:android
```

### Every time you change web code

```
npm run mobile:sync      # build + cap sync
```

### Signing + stores

- iOS: open `ios/App/App.xcworkspace` in Xcode, set Team + bundle identifier
  (matches `appId` in `capacitor.config.ts`: `za.co.sacryptotracker.app`),
  archive → App Store Connect. Needs Apple Developer membership ($99/yr).
- Android: `cd android && ./gradlew bundleRelease`, upload the `.aab` to
  Play Console. Needs a Google Play Developer account ($25 one-time).
