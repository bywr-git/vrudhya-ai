import { GrowthRadar } from "@/components/growth-radar";
import { getOpportunities } from "@/lib/api-client";

export default async function HomePage() {
  const liveRadar = await getOpportunities();
  const isLive = liveRadar !== null;
  const opportunities = liveRadar ?? [];

  return (
    <main className="dashboard" aria-labelledby="page-title">
      <header className="dashboard__header reveal reveal--one">
        <div>
          <p className="eyebrow">AI GROWTH LABORATORY / LUMI GIFTS</p>
          <h1 id="page-title">Growth Radar</h1>
          <p className="lede">Find what grows. Prove what works.</p>
        </div>
        <div className="system-status" aria-label="System status: observing">
          <span className="status-dot" aria-hidden="true" />
          <span>SYSTEM OBSERVING</span>
          <small>{isLive ? "LIVE API" : "DEMO VIEW"}</small>
        </div>
      </header>

      {!isLive && (
        <div className="demo-notice reveal reveal--two" role="status">
          <strong>DEMO PRESENTATION</strong>
          <span>Connect the FastAPI service to replace presentation placeholders with persisted Radar data.</span>
        </div>
      )}

      <section className="metric-grid reveal reveal--two" aria-label="Growth overview">
        <div className="metric-grid__item metric-grid__item--cyan"><span>REVENUE</span><strong>₹—</strong><small>AWAITING AGGREGATE API</small></div>
        <div className="metric-grid__item metric-grid__item--pink"><span>OPPORTUNITIES</span><strong>{isLive ? String(opportunities.length).padStart(2, "0") : "04"}</strong><small>{isLive ? "PERSISTED RADAR" : "DEMO PRESENTATION"}</small></div>
        <div className="metric-grid__item metric-grid__item--lime"><span>EXPERIMENTS</span><strong>—</strong><small>NO LIST API YET</small></div>
        <div className="metric-grid__item metric-grid__item--yellow"><span>LEARNINGS</span><strong>—</strong><small>NO SUMMARY API YET</small></div>
      </section>

      <GrowthRadar opportunities={opportunities} isLive={isLive} />
    </main>
  );
}