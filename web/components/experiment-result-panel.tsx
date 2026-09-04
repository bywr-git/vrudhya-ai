import type { MeasurementResponse } from "@/lib/api-types";

export function ExperimentResultPanel({ result }: { result: MeasurementResponse }) {
  return (
    <section className="experiment-result" aria-labelledby="measured-result-title">
      <div className="experiment-result__header"><div><span className="intel-label">EXPERIMENT / OBSERVED OUTCOME</span><h3 id="measured-result-title">Measured result</h3></div><strong className="phase-chip phase-chip--measured">MEASURED RESULT</strong></div>
      <div className="experiment-result__primary"><span className="intel-label">PRIMARY METRIC / {result.primary.metric}</span><div className="result-values"><div><span>CONTROL</span><strong>{result.primary.control_metric}</strong></div><div><span>VARIANT</span><strong>{result.primary.variant_metric}</strong></div></div></div>
      <div className="result-deltas"><div><span>ABSOLUTE DELTA</span><strong>{result.primary.absolute_difference}</strong></div><div><span>RELATIVE DELTA</span><strong>{result.primary.relative_difference ?? "—"}</strong></div></div>
      {result.guardrails.length > 0 && <div className="result-guardrails"><span className="intel-label">GUARDRAILS</span>{result.guardrails.map((guardrail) => <span key={guardrail.metric}>{guardrail.metric}: {guardrail.absolute_difference}</span>)}</div>}
      <div className="phase-panel__disclaimer phase-panel__disclaimer--measured">MEASURED / BACKEND-CALCULATED RESULT</div>
    </section>
  );
}