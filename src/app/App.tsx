import { useSnapshot } from "./hooks/useSnapshot";
import { PriceGrid } from "./components/PriceGrid";
import { relTime } from "./lib/format";

export default function App() {
  const state = useSnapshot();

  return (
    <div className="min-h-[100dvh]">
      <header className="safe-top border-b border-ink-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-4 sm:px-6 sm:py-5">
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold tracking-tight sm:text-lg">
              SA Crypto Tracker
            </h1>
            <p className="text-[11px] text-fog sm:text-xs">
              Observed prices across local exchanges. Not advice.
            </p>
          </div>
          <StatusPill state={state} />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
        {state.status === "loading" && (
          <p className="text-fog">Loading snapshot…</p>
        )}
        {state.status === "error" && !state.snapshot && (
          <p className="text-red-400">Could not load: {state.error}</p>
        )}
        {state.snapshot && <PriceGrid snapshot={state.snapshot} />}
      </main>

      <footer className="safe-bottom mx-auto max-w-5xl px-4 py-8 text-[11px] text-fog sm:px-6 sm:text-xs">
        Data is observed from public endpoints and may be delayed. This page
        does not offer financial advice.
      </footer>
    </div>
  );
}

function StatusPill({ state }: { state: ReturnType<typeof useSnapshot> }) {
  if (state.status === "loading") {
    return <span className="text-[11px] text-fog sm:text-xs">loading…</span>;
  }
  if (state.status === "error") {
    return (
      <span className="text-[11px] text-red-400 sm:text-xs">
        stale · {state.error}
      </span>
    );
  }
  return (
    <span className="text-[11px] text-fog sm:text-xs">
      {relTime(state.snapshot.generatedAt)}
    </span>
  );
}
