import type { SimulationResult } from "@/lib/api-types";

export function SimulationPanel({ simulation }: { simulation: SimulationResult }) {
  const outputs = simulation.outputs;
  return (
    <section className="phase-panel phase-panel--simulation" aria-labelledby="simulation-title">
      <div className="phase-panel__header"><div><span className="intel-label">SIMULATION / DETERMINISTIC</span><h3 id="simulation-title">What could happen?</h3></div><strong className="phase-chip phase-chip--simulated">SIMULATED</strong></div>
      <p className="phase-panel__intro">Before we test this in the real experiment, Vrudhya estimates what could happen.</p>
      <div className="simulation-values">
        <div><span>PRIMARY METRIC</span><strong>{String(outputs.primary_metric ?? "—")}</strong></div>
        <div><span>BASELINE</span><strong>{String(outputs.baseline_value ?? "—")} {String(outputs.unit ?? "")}</strong></div>
        <div><span>SIMULATED VALUE</span><strong>{String(outputs.simulated_value ?? "—")} {String(outputs.unit ?? "")}</strong></div>
        <div><span>RELATIVE LIFT</span><strong>{String(outputs.relative_lift ?? "—")}</strong></div>
      </div>
      <div className="phase-panel__trace"><span>ASSUMPTION HASH</span><code>{simulation.assumption_hash}</code><span>METHOD / {String(outputs.method ?? "PERSISTED SIMULATION")}</span></div>
      <div className="phase-panel__disclaimer">SIMULATION — NOT MEASURED RESULT</div>
    </section>
  );
}