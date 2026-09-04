import type { AuditLog } from "@/lib/api-types";

export function AuditTrailPanel({ logs }: { logs: AuditLog[] | null }) {
  return (
    <section className="audit-panel" aria-labelledby="audit-title">
      <div className="audit-panel__header"><div><span className="intel-label">TRACE / APPEND-ONLY RECORDS</span><h3 id="audit-title">Audit trail</h3></div><span className="phase-chip">BACKEND EVENTS</span></div>
      {logs === null ? <p className="intel-empty">AUDIT STREAM UNAVAILABLE.</p> : logs.length === 0 ? <p className="intel-empty">NO AUDIT RECORDS HAVE BEEN WRITTEN YET.</p> : <div className="audit-list">{logs.map((log) => <article key={log.id}><time dateTime={log.timestamp}>{new Date(log.timestamp).toLocaleString()}</time><div><strong>{log.action.replaceAll(".", " / ").toUpperCase()}</strong><p>{log.result}</p></div><span className={`audit-outcome audit-outcome--${log.permission_outcome}`}>{log.permission_outcome.replaceAll("_", " ").toUpperCase()}</span><code>{log.idempotency_key}</code></article>)}</div>}
    </section>
  );
}