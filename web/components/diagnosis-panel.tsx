import type { Diagnosis } from "@/lib/api-types";

export function DiagnosisPanel({ diagnosis }: { diagnosis: Diagnosis }) {
  return (
    <section className="intel-panel intel-panel--diagnosis" aria-labelledby="diagnosis-title">
      <div className="intel-panel__kicker"><span>02 / REASONING LAYER</span><b>AI DIAGNOSIS</b></div>
      <h3 id="diagnosis-title">Why this signal matters</h3>
      <p className="intel-panel__statement">{diagnosis.statement}</p>
      <div className="intel-panel__grid">
        <div><span className="intel-label">OBSERVED EVIDENCE</span><p>{diagnosis.supporting_fact_ids.length} persisted fact references</p></div>
        <div><span className="intel-label">UNCERTAINTY</span><p>{diagnosis.uncertainty}</p></div>
      </div>
      <footer className="intel-panel__footer">SOURCE / PERSISTED OPPORTUNITY <span>{diagnosis.model_version}</span></footer>
    </section>
  );
}