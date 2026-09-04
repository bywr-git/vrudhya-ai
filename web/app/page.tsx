import { GrowthRadar } from "@/components/growth-radar";
import { MetricCard } from "@/components/metric-card";
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
          <div className="system-status__top"><span className="radar-scan" aria-hidden="true"><i /></span><span>SYSTEM OBSERVING</span></div>
          <div className="system-status__readout"><strong>{isLive ? opportunities.length.toString().padStart(2, "0") : "12"}</strong><span>FACTS</span><strong>{isLive ? "01" : "01"}</strong><span>SIGNAL</span></div>
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
        <MetricCard label="REVENUE" value="₹—" detail="AWAITING AGGREGATE API" tone="paper" motif="signal" />
        <MetricCard label="OPPORTUNITIES" value={isLive ? String(opportunities.length).padStart(2, "0") : "04"} detail={isLive ? "PERSISTED RADAR" : "DEMO PRESENTATION"} tone="violet" motif="radar" />
        <MetricCard label="EXPERIMENTS" value="—" detail="NO LIST API YET" tone="chartreuse" motif="nodes" />
        <MetricCard label="LEARNINGS" value="—" detail="NO SUMMARY API YET" tone="orange" motif="branch" />
      </section>

      <GrowthRadar opportunities={opportunities} isLive={isLive} />
    </main>
  );
}