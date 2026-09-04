import type { PermissionDecision } from "@/lib/api-types";

const labels = { allowed: "ALLOWED", approval_required: "APPROVAL REQUIRED", denied: "DENIED" } as const;

export function PermissionPanel({ permission, onContinue }: { permission: PermissionDecision; onContinue: () => void }) {
  return (
    <section className={`phase-panel phase-panel--permission phase-panel--${permission.outcome}`} aria-labelledby="permission-title">
      <div className="phase-panel__header"><div><span className="intel-label">PERMISSION / DETERMINISTIC POLICY</span><h3 id="permission-title">Can this action proceed?</h3></div><strong className="phase-chip">{labels[permission.outcome]}</strong></div>
      <p className="phase-panel__intro">{permission.reason}</p>
      {permission.action_type.startsWith("razorpay_") && <div className="razorpay-marker">RAZORPAY TEST MODE / APPROVAL GATED</div>}
      <div className="permission-readout"><span className="permission-readout__mark" aria-hidden="true">{permission.outcome === "allowed" ? "✓" : permission.outcome === "denied" ? "×" : "!"}</span><div><span className="intel-label">ACTION TYPE</span><strong>{permission.action_type}</strong></div></div>
      {permission.outcome !== "denied" && <button type="button" className="phase-button" onClick={onContinue}>VIEW EXPERIMENT DRAFT →</button>}
      {permission.outcome === "denied" && <p className="phase-panel__warning">PERMISSION DENIED → ACTION NOT EXECUTED. Vrudhya will not bypass this decision.</p>}
    </section>
  );
}