import { useSnapshot } from "./hooks/useSnapshot";
import { PriceGrid } from "./components/PriceGrid";
import { relTime } from "./lib/format";

export default function App() {
  const state = useSnapshot();

  return (
    <div className="min-h-screen">
      <header className="border-b border-ink-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">
              SA Crypto Tracker
            </h1>
            <p className="text-xs text-fog">
              Observed prices across local exchanges. Not advice.
            </p>
          </div>
          <StatusPill state={state} />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {state.status === "loading" && (
          <p className="text-fog">Loading snapshot…</p>
        )}
        {state.status === "error" && !state.snapshot && (
          <p className="text-red-400">Could not load: {state.error}</p>
        )}
        {state.snapshot && <PriceGrid snapshot={state.snapshot} />}
      </main>

      <footer className="mx-auto max-w-5xl px-6 py-10 text-xs text-fog">
        Data is observed from public endpoints and may be delayed. This page
        does not offer financial advice.
      </footer>
    </div>
  );
}

function StatusPill({ state }: { state: ReturnType<typeof useSnapshot> }) {
  if (state.status === "loading") {
    return <span className="text-xs text-fog">loading…</span>;
  }
  if (state.status === "error") {
    return <span className="text-xs text-red-400">stale · {state.error}</span>;
  }
  return (
    <span className="text-xs text-fog">
      updated {relTime(state.snapshot.generatedAt)}
    </span>
  );
}
