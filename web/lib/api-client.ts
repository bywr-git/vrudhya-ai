import type { Opportunity, OpportunityDetail } from "@/lib/api-types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { headers: { Accept: "application/json" }, cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export function getOpportunities() { return get<Opportunity[]>("/v1/opportunities"); }
export function getOpportunity(id: string) { return get<OpportunityDetail>(`/v1/opportunities/${encodeURIComponent(id)}`); }