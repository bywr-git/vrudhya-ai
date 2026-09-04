import type { Hypothesis } from "@/lib/api-types";
import { StatusBadge } from "@/components/status-badge";

export function HypothesisPanel({ hypotheses }: { hypotheses: Hypothesis[] }) {
  return (
    <section className="intel-panel intel-panel--hypotheses" aria-labelledby="hypotheses-title">
      <div className="intel-panel__kicker"><span>03 / RESEARCH SPACE</span><b>HYPOTHESES</b></div>
      <h3 id="hypotheses-title">Competing explanations</h3>
      {hypotheses.length === 0 ? <p className="intel-empty">NO PERSISTED HYPOTHESES YET.</p> : <ol className="hypothesis-list">
        {hypotheses.map((hypothesis, index) => <li key={hypothesis.id}><span className="hypothesis-list__number">{String(index + 1).padStart(2, "0")}</span><div><span className="intel-label">HYPOTHESIS / {hypothesis.status.toUpperCase()}</span><p>{hypothesis.statement}</p><small>SUPPORTED BY {hypothesis.supporting_fact_ids.length} OBSERVED FACTS</small></div><StatusBadge status={hypothesis.status} /></li>)}
      </ol>}
    </section>
  );
}