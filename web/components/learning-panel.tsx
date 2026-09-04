import type { AgentLoopResponse, GrowthDnaEntry, LearningResponse } from "@/lib/api-types";

type LearningPanelProps = { learning: LearningResponse; dna: GrowthDnaEntry | null; continuing: boolean; continuation: AgentLoopResponse | null; onContinue: () => void };

export function LearningPanel({ learning, dna, continuing, continuation, onContinue }: LearningPanelProps) {
  const outcomeClass = `learning-panel--${learning.outcome}`;
  const canContinue = !continuation && (learning.outcome === "supported" || learning.outcome === "rejected");
  return (
    <section className={`learning-panel ${outcomeClass}`} aria-labelledby="learning-title">
      <div className="learning-panel__header"><div><span className="intel-label">10 / MEASURED EVIDENCE</span><h3 id="learning-title">Learn from result</h3></div><strong className="phase-chip">{learning.outcome.toUpperCase()}</strong></div>
      <div className="learning-panel__claim"><span>CLAIM TYPE</span><strong>{learning.claim_type.toUpperCase()}</strong></div>
      <p className="learning-panel__explanation">{learning.explanation}</p>
      <div className="learning-panel__trace"><span>EXPERIMENT / {learning.experiment_id}</span><span>RESULT / {learning.experiment_result_id}</span><span>GROWTH DNA / {learning.growth_dna_updated ? "UPDATED" : "UNCHANGED"}</span></div>
      {dna && <div className="learning-panel__dna"><span className="intel-label">LEARNED FROM MEASURED EVIDENCE</span><strong>{dna.kind.replaceAll("_", " ").toUpperCase()}</strong><p>{String(dna.body.explanation ?? "Persisted merchant learning")}</p><small>EVIDENCE EXPERIMENT / {dna.evidence_experiment_id ?? learning.experiment_id}</small></div>}
      {learning.outcome === "inconclusive" && <p className="learning-panel__stop">INCONCLUSIVE — THE LEARNING LOOP STOPS HERE. NO EXECUTION PATH IS SUGGESTED.</p>}
      {canContinue && <button type="button" className="phase-button" onClick={onContinue} disabled={continuing}>{continuing ? "CONTINUING LOOP" : "CONTINUE →"}</button>}
      {continuation && <div className="learning-panel__next"><span className="intel-label">NEXT OPPORTUNITY</span><strong>{continuation.next_opportunity_id ?? "NONE CREATED"}</strong><p>STAGE / {continuation.next_stage.toUpperCase()}</p></div>}
    </section>
  );
}