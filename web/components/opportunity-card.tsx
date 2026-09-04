import type { Opportunity } from "@/lib/api-types";
import { StatusBadge } from "@/components/status-badge";

export function OpportunityCard({ opportunity, demo = false }: { opportunity: Opportunity; demo?: boolean }) {
  return (
    <article className="opportunity-card reveal reveal--three">
      <div className="card__top"><span className="card__meta">{demo ? "OPPORTUNITY_014" : `OPPORTUNITY_${opportunity.id.slice(0, 6).toUpperCase()}`}</span><StatusBadge status={opportunity.status} /></div>
      <div>
        <h3 className="card__title">{demo ? "PDP CONVERSION" : opportunity.detector_id.replaceAll("_", " ")}</h3>
        <p className="card__entity">{demo ? "Product detail page / Lumi Surprise Gift" : `${opportunity.entity_type} / ${opportunity.entity_id}`}</p>
      </div>
      <div className="card__footer"><p className="card__evidence">{demo ? "CLAIM_TYPE: OBSERVATION / EVIDENCE READY" : `${opportunity.evidence_fact_ids.length} EVIDENCE FACTS / SCORE ${opportunity.score}`}</p><a className="card__action" href={demo ? "#radar" : `/opportunities/${opportunity.id}`}>INVESTIGATE →</a></div>
    </article>
  );
}