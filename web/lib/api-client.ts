import type { AgentLoopResponse, Diagnosis, ExecutionResponse, ExperimentDraft, GrowthDnaEntry, HypothesesResponse, LearningResponse, MeasurementResponse, Opportunity, OpportunityDetail, RunResponse, StrategiesResponse } from "@/lib/api-types";

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

async function post<T>(path: string, body?: unknown): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { method: "POST", headers: { Accept: "application/json", ...(body === undefined ? {} : { "Content-Type": "application/json" }) }, body: body === undefined ? undefined : JSON.stringify(body), cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export function getOpportunities() { return get<Opportunity[]>("/v1/opportunities"); }
export function getOpportunity(id: string) { return get<OpportunityDetail>(`/v1/opportunities/${encodeURIComponent(id)}`); }
export function diagnoseOpportunity(id: string) { return post<Record<string, unknown>>(`/v1/opportunities/${encodeURIComponent(id)}/diagnose`); }
export function getDiagnosis(id: string) { return get<Diagnosis>(`/v1/opportunities/${encodeURIComponent(id)}/diagnosis`); }
export function getHypotheses(id: string) { return get<HypothesesResponse>(`/v1/opportunities/${encodeURIComponent(id)}/hypotheses`); }
export function getStrategies(id: string) { return get<StrategiesResponse>(`/v1/opportunities/${encodeURIComponent(id)}/strategies`); }
export function createExperimentDraft(strategyId: string) { return post<ExperimentDraft>(`/v1/experiments/draft/${encodeURIComponent(strategyId)}`); }
export function approveExperiment(id: string) { return post<ExecutionResponse>(`/v1/experiments/${encodeURIComponent(id)}/approve`, { approved: true }); }
export function rejectExperiment(id: string) { return post<ExecutionResponse>(`/v1/experiments/${encodeURIComponent(id)}/reject`); }
export function runExperiment(id: string) { return post<RunResponse>(`/v1/experiments/${encodeURIComponent(id)}/run`); }
export function measureExperiment(id: string) { return post<MeasurementResponse>(`/v1/experiments/${encodeURIComponent(id)}/measure`); }
export function learnFromExperiment(id: string) { return post<LearningResponse>(`/v1/learning/experiments/${encodeURIComponent(id)}/learn`); }
export function continueAgentLoop(id: string) { return post<AgentLoopResponse>(`/v1/learning/experiments/${encodeURIComponent(id)}/continue`); }
export function getGrowthDna() { return get<GrowthDnaEntry[]>("/v1/learning/growth-dna"); }