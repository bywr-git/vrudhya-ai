type MetricCardProps = { label: string; value: string; detail: string; tone: "cyan" | "pink" | "lime" | "yellow" };

export function MetricCard({ label, value, detail, tone }: MetricCardProps) {
  return <div className={`metric-grid__item metric-grid__item--${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}