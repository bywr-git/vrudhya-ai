import type { GrowthDnaEntry } from "@/lib/api-types";

export function GrowthDnaPanel({ entries }: { entries: GrowthDnaEntry[] }) {
  return (
    <section className="growth-dna-panel" aria-labelledby="growth-dna-title">
      <div className="growth-dna-panel__header"><div><span className="intel-label">MERCHANT MEMORY / PERSISTED</span><h3 id="growth-dna-title">Growth DNA</h3></div><span className="phase-chip">MEASURED ONLY</span></div>
      {entries.length === 0 ? <p className="intel-empty">NO LEARNED EVIDENCE YET. MEASURED RESULTS WILL APPEAR HERE.</p> : <div className="growth-dna-list">{entries.map((entry) => <article key={entry.id}><div><span className="intel-label">{entry.kind.replaceAll("_", " ").toUpperCase()}</span><h4>{entry.key}</h4><p>{String(entry.body.explanation ?? "Persisted merchant learning")}</p></div><small>EVIDENCE EXPERIMENT<br />{entry.evidence_experiment_id ?? "—"}</small></article>)}</div>}
    </section>
  );
}