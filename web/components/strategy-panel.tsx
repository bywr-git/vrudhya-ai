import type { Strategy } from "@/lib/api-types";

export function StrategyPanel({ strategies, onSimulate, simulatingStrategyId }: { strategies: Strategy[]; onSimulate: (strategy: Strategy) => void; simulatingStrategyId: string | null }) {
  return (
    <section className="intel-panel intel-panel--strategy" aria-labelledby="strategy-title">
      <div className="intel-panel__kicker"><span>04 / INTERVENTION DESIGN</span><b>STRATEGY</b></div>
      <h3 id="strategy-title">Persisted intervention</h3>
      {strategies.length === 0 ? <p className="intel-empty">NO PERSISTED STRATEGIES YET.</p> : <div className="strategy-list">
        {strategies.map((strategy, index) => <article key={strategy.id}><div className="strategy-list__number">{String(index + 1).padStart(2, "0")}</div><div><span className="intel-label">{strategy.action_type.toUpperCase()}</span><p>{strategy.rationale}</p><div className="strategy-meta"><span>PRIMARY / {strategy.primary_metric}</span><span>GUARDS / {strategy.guardrail_metrics.join(", ")}</span></div></div><button type="button" className="next-phase-button next-phase-button--active" onClick={() => onSimulate(strategy)} disabled={simulatingStrategyId !== null}>{simulatingStrategyId === strategy.id ? "RUNNING SIMULATION" : "SIMULATE →"}</button></article>)}
      </div>}
    </section>
  );
}