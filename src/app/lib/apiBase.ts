import { Capacitor } from "@capacitor/core";

// On web the app and API share an origin (/api is proxied or co-located on
// Cloudflare Pages). Inside Capacitor the web bundle is served from
// capacitor://localhost, so fetches must go to the deployed Worker URL.
// Set VITE_API_BASE at build time for native builds.
const NATIVE_BASE = import.meta.env.VITE_API_BASE ?? "";

export function apiUrl(path: string): string {
  if (Capacitor.isNativePlatform() && NATIVE_BASE) {
    return `${NATIVE_BASE.replace(/\/$/, "")}${path}`;
  }
  return path;
}
