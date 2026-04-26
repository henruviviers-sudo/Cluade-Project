import type { Snapshot } from "../shared/types";
import { TRACKED_PAIRS } from "../shared/types";
import { fetchLuno } from "./adapters/luno";
import { fetchValr } from "./adapters/valr";
import { fetchAltCoinTrader } from "./adapters/altcointrader";

interface Env {
  ASSETS?: Fetcher;
  SNAPSHOT_CACHE?: KVNamespace;
}

const CACHE_KEY = "snapshot:v1";
const CACHE_TTL_SECONDS = 15;

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/api/snapshot" || url.pathname === "/snapshot") {
      return handleSnapshot(env);
    }
    if (url.pathname === "/api/health" || url.pathname === "/health") {
      return json({ ok: true, at: Date.now() });
    }

    if (env.ASSETS) return env.ASSETS.fetch(request);
    return new Response("not found", { status: 404 });
  },

  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil(refreshSnapshot(env));
  },
};

async function buildSnapshot(): Promise<Snapshot> {
  const pairs = [...TRACKED_PAIRS];
  const [luno, valr, act] = await Promise.all([
    fetchLuno(pairs),
    fetchValr(pairs),
    fetchAltCoinTrader(pairs),
  ]);
  return { generatedAt: Date.now(), exchanges: [luno, valr, act] };
}

async function refreshSnapshot(env: Env): Promise<void> {
  const snapshot = await buildSnapshot();
  if (env.SNAPSHOT_CACHE) {
    await env.SNAPSHOT_CACHE.put(CACHE_KEY, JSON.stringify(snapshot), {
      expirationTtl: CACHE_TTL_SECONDS,
    });
  }
}

async function handleSnapshot(env: Env): Promise<Response> {
  if (env.SNAPSHOT_CACHE) {
    const cached = await env.SNAPSHOT_CACHE.get(CACHE_KEY);
    if (cached) return jsonRaw(cached, { "x-cache": "hit" });
  }

  const snapshot = await buildSnapshot();
  const body = JSON.stringify(snapshot);
  if (env.SNAPSHOT_CACHE) {
    await env.SNAPSHOT_CACHE.put(CACHE_KEY, body, {
      expirationTtl: CACHE_TTL_SECONDS,
    });
  }
  return jsonRaw(body, { "x-cache": "miss" });
}

function json(data: unknown, extra: Record<string, string> = {}): Response {
  return jsonRaw(JSON.stringify(data), extra);
}

function jsonRaw(body: string, extra: Record<string, string> = {}): Response {
  return new Response(body, {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": `public, max-age=${CACHE_TTL_SECONDS}`,
      "access-control-allow-origin": "*",
      ...extra,
    },
  });
}
