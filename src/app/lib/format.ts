const ZAR = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
  maximumFractionDigits: 2,
});

export function zar(n: number | null): string {
  if (n === null) return "—";
  return ZAR.format(n);
}

export function relTime(ms: number): string {
  const diff = Date.now() - ms;
  if (diff < 1_000) return "just now";
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`;
  return `${Math.round(diff / 60_000)}m ago`;
}
