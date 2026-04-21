import type { Snapshot, TrackedPair } from "../../shared/types";
import { TRACKED_PAIRS } from "../../shared/types";
import { zar } from "../lib/format";

interface Props {
  snapshot: Snapshot;
}

export function PriceGrid({ snapshot }: Props) {
  return (
    <div className="overflow-x-auto rounded-lg border border-ink-line">
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

function Row({
  pair,
  snapshot,
}: {
  pair: TrackedPair;
  snapshot: Snapshot;
}) {
  const lasts: number[] = [];
  const cells = snapshot.exchanges.map((ex) => {
    const t = ex.tickers.find((x) => x.pair === pair);
    if (t?.last != null) lasts.push(t.last);
    return { exchange: ex.exchange, last: t?.last ?? null };
  });

  const spread =
    lasts.length >= 2
      ? ((Math.max(...lasts) - Math.min(...lasts)) / Math.min(...lasts)) * 100
      : null;

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
