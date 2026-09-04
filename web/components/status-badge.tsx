const labels: Record<string, string> = {
  open: "DETECTED", investigating: "DIAGNOSING", simulating: "SIMULATING", awaiting_approval: "AWAITING APPROVAL",
  approved: "APPROVED", running: "RUNNING", measured: "MEASURED", supported: "SUPPORTED", rejected: "REJECTED", inconclusive: "INCONCLUSIVE",
};

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  return <span className={`status-badge status-badge--${normalized.replaceAll("_", "-")}`}>{labels[normalized] ?? normalized.replaceAll("_", " ").toUpperCase()}</span>;
}