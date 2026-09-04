import type { Opportunity } from "@/lib/api-types";
import { StatusBadge } from "@/components/status-badge";

export function OpportunityCard({ opportunity, demo = false, onSelect }: { opportunity: Opportunity; demo?: boolean; onSelect?: () => void }) {
  return (
    <article className={`opportunity-card reveal reveal--three ${onSelect ? "opportunity-card--interactive" : ""}`}>
      <div className="card__top"><span className="card__meta">{demo ? "OPPORTUNITY_014" : `OPPORTUNITY_${opportunity.id.slice(0, 6).toUpperCase()}`}</span><StatusBadge status={opportunity.status} /></div>
      <div className="card__finding">
        <span className="finding-signal" aria-hidden="true"><i /><b /><em /></span>
        <h3 className="card__title">{demo ? "PDP CONVERSION" : opportunity.detector_id.replaceAll("_", " ")}</h3>
        <p className="card__entity">{demo ? "Product detail page / Lumi Surprise Gift" : `${opportunity.entity_type} / ${opportunity.entity_id}`}</p>
      </div>
      <div className="card__footer"><p className="card__evidence">{demo ? "CLAIM_TYPE: OBSERVATION / EVIDENCE READY" : `${opportunity.evidence_fact_ids.length} EVIDENCE FACTS / SCORE ${opportunity.score}`}</p>{onSelect ? <button type="button" className="card__action" onClick={onSelect}>INSPECT →</button> : <a className="card__action" href="#radar">DIAGNOSE →</a>}</div>
    </article>
  );
}