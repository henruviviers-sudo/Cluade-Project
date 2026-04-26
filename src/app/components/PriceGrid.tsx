import type { Snapshot, TrackedPair } from "../../shared/types";
import { TRACKED_PAIRS } from "../../shared/types";
import { zar } from "../lib/format";

interface Props {
  snapshot: Snapshot;
}

export function PriceGrid({ snapshot }: Props) {
  return (
    <>
      <MobileCards snapshot={snapshot} />
      <DesktopTable snapshot={snapshot} />
    </>
  );
}

function MobileCards({ snapshot }: Props) {
  return (
    <div className="grid gap-3 sm:hidden">
      {TRACKED_PAIRS.map((pair) => {
        const perExchange = snapshot.exchanges.map((ex) => {
          const t = ex.tickers.find((x) => x.pair === pair);
          return { exchange: ex.exchange, ok: ex.ok, last: t?.last ?? null };
        });
        const lasts = perExchange
          .map((p) => p.last)
          .filter((n): n is number => n !== null);
        const spread = spreadPct(lasts);

        return (
          <div
            key={pair}
            className="rounded-xl border border-ink-line bg-ink-soft p-4"
          >
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-base">{pair}</span>
              <span className="text-xs text-fog">
                {spread === null ? "—" : `spread ${spread.toFixed(2)}%`}
              </span>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              {perExchange.map((p) => (
                <div
                  key={p.exchange}
                  className="flex items-baseline justify-between"
                >
                  <dt className="capitalize text-fog">
                    {p.exchange}
                    {!p.ok && (
                      <span className="ml-1 text-[10px] text-red-400">
                        offline
                      </span>
                    )}
                  </dt>
                  <dd className="font-mono tabular-nums">{zar(p.last)}</dd>
                </div>
              ))}
            </dl>
          </div>
        );
      })}
    </div>
  );
}

function DesktopTable({ snapshot }: Props) {
  return (
    <div className="hidden overflow-x-auto rounded-lg border border-ink-line sm:block">
      <table className="w-full text-sm">
        <thead className="bg-ink-soft text-fog">
          <tr>
            <th className="px-4 py-3 text-left font-normal">Pair</th>
            {snapshot.exchanges.map((ex) => (
              <th
                key={ex.exchange}
                className="px-4 py-3 text-right font-normal capitalize"
              >
                {ex.exchange}
                {!ex.ok && (
                  <span className="ml-2 text-xs text-red-400">offline</span>
                )}
              </th>
            ))}
            <th className="px-4 py-3 text-right font-normal">Spread</th>
          </tr>
        </thead>
        <tbody>
          {TRACKED_PAIRS.map((pair) => (
            <Row key={pair} pair={pair} snapshot={snapshot} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Row({ pair, snapshot }: { pair: TrackedPair; snapshot: Snapshot }) {
  const cells = snapshot.exchanges.map((ex) => {
    const t = ex.tickers.find((x) => x.pair === pair);
    return { exchange: ex.exchange, last: t?.last ?? null };
  });
  const lasts = cells
    .map((c) => c.last)
    .filter((n): n is number => n !== null);
  const spread = spreadPct(lasts);

  return (
    <tr className="border-t border-ink-line">
      <td className="px-4 py-3 font-mono">{pair}</td>
      {cells.map((c) => (
        <td
          key={c.exchange}
          className="px-4 py-3 text-right font-mono tabular-nums"
        >
          {zar(c.last)}
        </td>
      ))}
      <td className="px-4 py-3 text-right font-mono tabular-nums text-fog">
        {spread === null ? "—" : `${spread.toFixed(2)}%`}
      </td>
    </tr>
  );
}

function spreadPct(values: number[]): number | null {
  if (values.length < 2) return null;
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  return ((hi - lo) / lo) * 100;
}
