// Set VITE_API_BASE at build time to point at the deployed Worker.
// Required for Capacitor (capacitor://localhost can't resolve relative
// paths) and for web builds where the frontend and Worker are on
// different origins. Empty falls back to same-origin (dev proxy).
const BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

export function apiUrl(path: string): string {
  return BASE ? `${BASE}${path}` : path;
}
