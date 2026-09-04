type MetricCardProps = { label: string; value: string; detail: string; tone: "paper" | "violet" | "chartreuse" | "orange"; motif: "signal" | "radar" | "nodes" | "branch" };

export function MetricCard({ label, value, detail, tone, motif }: MetricCardProps) {
  return <div className={`metric-grid__item metric-grid__item--${tone}`}><span>{label}</span><strong>{value}</strong><span className={`metric-motif metric-motif--${motif}`} aria-hidden="true" /><small>{detail}</small></div>;
}