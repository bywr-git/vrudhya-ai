"use client";

import { useState } from "react";
import type { Opportunity } from "@/lib/api-types";
import { OpportunityCard } from "@/components/opportunity-card";
import { OpportunityDetail } from "@/components/opportunity-detail";

const flow = ["OBSERVE", "DETECT", "DIAGNOSE", "STRATEGIZE", "EXPERIMENT", "MEASURE", "LEARN"];

export function GrowthRadar({ opportunities, isLive }: { opportunities: Opportunity[]; isLive: boolean }) {
  const [selected, setSelected] = useState<Opportunity | null>(null);
  return (
    <section className="radar reveal reveal--three" id="radar" aria-labelledby="radar-title">
      <div className="radar__heading"><h2 id="radar-title">Growth Radar</h2><p>{isLive ? "PERSISTED DETECTOR OUTPUT" : "DEMO OPPORTUNITY BOARD"}</p></div>
      <div className="flow" aria-label="Observe to learn process">{flow.map((step, index) => <div className={`flow__step ${index === 1 ? "flow__step--active" : ""}`} key={step}><span className="flow__number">0{index + 1}</span><span>{step}</span><i aria-hidden="true" /></div>)}</div>
      <div className="cards">
        {isLive && opportunities.map((opportunity) => <OpportunityCard key={opportunity.id} opportunity={opportunity} onSelect={() => setSelected(opportunity)} />)}
        {!isLive && <OpportunityCard demo opportunity={{ id: "demo", merchant_id: "demo", detector_id: "high_traffic_low_conversion", entity_type: "product", entity_id: "demo", score: "0", evidence_fact_ids: [], status: "open", created_at: "", updated_at: "" }} />}
        {isLive && opportunities.length === 0 && <div className="empty-state">NO OPEN OPPORTUNITIES IN THE CURRENT RADAR SNAPSHOT.</div>}
      </div>
      {selected && <OpportunityDetail opportunity={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}