import { useEffect, useRef, useState } from "react";
import type { Snapshot } from "../../shared/types";
import { apiUrl } from "../lib/apiBase";

type State =
  | { status: "loading"; snapshot: null; error: null }
  | { status: "ready"; snapshot: Snapshot; error: null }
  | { status: "error"; snapshot: Snapshot | null; error: string };

const DEFAULT_INTERVAL_MS = 15_000;

export function useSnapshot(intervalMs: number = DEFAULT_INTERVAL_MS): State {
  const [state, setState] = useState<State>({
    status: "loading",
    snapshot: null,
    error: null,
  });
  const lastRef = useRef<Snapshot | null>(null);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function load() {
      try {
        const res = await fetch(apiUrl("/api/snapshot"), {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`snapshot ${res.status}`);
        const snap = (await res.json()) as Snapshot;
        if (cancelled) return;
        lastRef.current = snap;
        setState({ status: "ready", snapshot: snap, error: null });
      } catch (err) {
        if (cancelled) return;
        if ((err as Error).name === "AbortError") return;
        setState({
          status: "error",
          snapshot: lastRef.current,
          error: (err as Error).message,
        });
      }
    }

    load();
    const id = window.setInterval(load, intervalMs);
    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(id);
    };
  }, [intervalMs]);

  return state;
}
