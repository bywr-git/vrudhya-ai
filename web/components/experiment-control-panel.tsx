import type { Experiment } from "@/lib/api-types";
import { StatusBadge } from "@/components/status-badge";

type Action = "approve" | "reject" | "run" | "measure";

export function ExperimentControlPanel({ experiment, loading, onAction, error }: { experiment: Experiment; loading: Action | null; onAction: (action: Action) => void; error: string | null }) {
  const status = experiment.status;
  return (
    <section className="experiment-control" aria-labelledby="experiment-control-title">
      <div className="experiment-control__header"><div><span className="intel-label">EXPERIMENT CONTROL / EXPLICIT ACTION</span><h3 id="experiment-control-title">Lifecycle gate</h3></div><StatusBadge status={status} /></div>
      {error && <p className="experiment-control__error" role="alert">{error}</p>}
      {status === "awaiting_approval" && <div className="experiment-control__actions"><button type="button" className="phase-button" onClick={() => onAction("approve")} disabled={loading !== null}>{loading === "approve" ? "APPROVING EXPERIMENT" : "APPROVE EXPERIMENT"}</button><button type="button" className="control-button control-button--reject" onClick={() => onAction("reject")} disabled={loading !== null}>{loading === "reject" ? "REJECTING" : "REJECT"}</button></div>}
      {status === "approved" && <div className="experiment-control__actions"><button type="button" className="phase-button" onClick={() => onAction("run")} disabled={loading !== null}>{loading === "run" ? "RUNNING EXPERIMENT" : "RUN EXPERIMENT →"}</button></div>}
      {status === "running" && <div className="experiment-control__actions"><div className="control-state">EXPERIMENT RUNNING</div><button type="button" className="phase-button" onClick={() => onAction("measure")} disabled={loading !== null}>{loading === "measure" ? "MEASURING EXPERIMENT" : "MEASURE EXPERIMENT →"}</button></div>}
      {status === "rejected_by_merchant" && <p className="control-state control-state--warning">REJECTED — THIS EXPERIMENT WILL NOT RUN.</p>}
      {status === "measured" && <p className="control-state control-state--complete">MEASUREMENT COMPLETE</p>}
    </section>
  );
}