import type { Experiment } from "@/lib/api-types";
import { StatusBadge } from "@/components/status-badge";

export function ExperimentDraftPanel({ experiment }: { experiment: Experiment }) {
  return (
    <section className="phase-panel phase-panel--draft" aria-labelledby="draft-title">
      <div className="phase-panel__header"><div><span className="intel-label">EXPERIMENT / PERSISTED DRAFT</span><h3 id="draft-title">Ready for the next gate</h3></div><StatusBadge status={experiment.status} /></div>
      <div className="draft-grid">
        <div><span>ID</span><strong>{experiment.id.slice(0, 8).toUpperCase()}</strong></div><div><span>ACTION TYPE</span><strong>{experiment.action_type}</strong></div><div><span>PRIMARY METRIC</span><strong>{experiment.primary_metric}</strong></div><div><span>WINDOW</span><strong>{experiment.window}</strong></div><div><span>MINIMUM SAMPLE</span><strong>{experiment.min_sample}</strong></div><div><span>GUARDRAILS</span><strong>{experiment.guardrail_metrics.join(", ") || "—"}</strong></div>
      </div>
      <div className="draft-descriptions"><div><span className="intel-label">CONTROL</span><p>{experiment.control_description}</p></div><div><span className="intel-label">VARIANT</span><p>{experiment.variant_description}</p></div></div>
      <p className="phase-panel__warning">DRAFT ONLY — approval and execution remain separate later steps.</p>
    </section>
  );
}