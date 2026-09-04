"use client";

import { useEffect, useState } from "react";
import { approveExperiment, continueAgentLoop, createExperimentDraft, diagnoseOpportunity, getAuditLogs, getDiagnosis, getGrowthDna, getHypotheses, getOpportunity, getStrategies, learnFromExperiment, measureExperiment, rejectExperiment, runExperiment } from "@/lib/api-client";
import type { AgentLoopResponse, AuditLog, Diagnosis, ExperimentDraft, GrowthDnaEntry, Hypothesis, LearningResponse, MeasurementResponse, Opportunity, OpportunityDetail as OpportunityDetailData, Strategy } from "@/lib/api-types";
import { StatusBadge } from "@/components/status-badge";
import { DiagnosisPanel } from "@/components/diagnosis-panel";
import { HypothesisPanel } from "@/components/hypothesis-panel";
import { StrategyPanel } from "@/components/strategy-panel";
import { SimulationPanel } from "@/components/simulation-panel";
import { PermissionPanel } from "@/components/permission-panel";
import { ExperimentDraftPanel } from "@/components/experiment-draft-panel";
import { ExperimentControlPanel } from "@/components/experiment-control-panel";
import { ExperimentResultPanel } from "@/components/experiment-result-panel";
import { LearningPanel } from "@/components/learning-panel";
import { GrowthDnaPanel } from "@/components/growth-dna-panel";
import { AuditTrailPanel } from "@/components/audit-trail-panel";

type WorkspaceState = "signal" | "diagnosing" | "diagnosed" | "simulating" | "simulation" | "permission" | "draft" | "approved" | "running" | "measured" | "error";

export function OpportunityDetail({ opportunity, onClose }: { opportunity: Opportunity; onClose: () => void }) {
  const [detail, setDetail] = useState<OpportunityDetailData | null>(null);
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [draft, setDraft] = useState<ExperimentDraft | null>(null);
  const [measurement, setMeasurement] = useState<MeasurementResponse | null>(null);
  const [learning, setLearning] = useState<LearningResponse | null>(null);
  const [growthDna, setGrowthDna] = useState<GrowthDnaEntry[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[] | null>(null);
  const [continuation, setContinuation] = useState<AgentLoopResponse | null>(null);
  const [learningLoading, setLearningLoading] = useState(false);
  const [continuing, setContinuing] = useState(false);
  const [simulatingStrategyId, setSimulatingStrategyId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<"approve" | "reject" | "run" | "measure" | null>(null);
  const [state, setState] = useState<WorkspaceState>("signal");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getOpportunity(opportunity.id).then((result) => {
      if (!active) return;
      if (result) setDetail(result);
      else setError("OPPORTUNITY SIGNAL UNAVAILABLE.");
    });
    void getAuditLogs().then(setAuditLogs);
    return () => { active = false; };
  }, [opportunity.id]);

  async function diagnose() {
    setState("diagnosing");
    setError(null);
    const created = await diagnoseOpportunity(opportunity.id);
    if (!created) { setState("error"); setError("THE SIGNAL COULD NOT BE DIAGNOSED. TRY AGAIN."); return; }
    const [nextDiagnosis, nextHypotheses, nextStrategies] = await Promise.all([
      getDiagnosis(opportunity.id), getHypotheses(opportunity.id), getStrategies(opportunity.id),
    ]);
    if (!nextDiagnosis) { setState("error"); setError("DIAGNOSIS WAS CREATED BUT COULD NOT BE READ."); return; }
    setDiagnosis(nextDiagnosis);
    setHypotheses(nextHypotheses?.hypotheses ?? []);
    setStrategies(nextStrategies?.strategies ?? []);
    setState("diagnosed");
  }

  async function simulate(strategy: Strategy) {
    setState("simulating");
    setSimulatingStrategyId(strategy.id);
    setError(null);
    const result = await createExperimentDraft(strategy.id);
    setSimulatingStrategyId(null);
    if (!result) { setState("error"); setError("THE LIVE API COULD NOT RUN THIS SIMULATION."); return; }
    setDraft(result);
    setState("simulation");
  }

  async function experimentAction(action: "approve" | "reject" | "run" | "measure") {
    if (!draft?.experiment) return;
    setActionLoading(action);
    setError(null);
    const experimentId = draft.experiment.id;
    const response = action === "approve" ? await approveExperiment(experimentId) : action === "reject" ? await rejectExperiment(experimentId) : action === "run" ? await runExperiment(experimentId) : await measureExperiment(experimentId);
    setActionLoading(null);
    if (!response) { setError(`${action.toUpperCase()} FAILED — THE BACKEND DID NOT CONFIRM THE ACTION.`); return; }
    if (action === "measure") {
      setMeasurement(response as MeasurementResponse);
      setDraft((current) => current ? { ...current, experiment: current.experiment ? { ...current.experiment, status: "measured" } : null } : current);
      setState("measured");
      return;
    }
    const status = response.status;
    setDraft((current) => current ? { ...current, experiment: current.experiment ? { ...current.experiment, status, approval_id: "approval_id" in response ? response.approval_id : current.experiment.approval_id } : null } : current);
    setState(status === "approved" ? "approved" : status === "running" ? "running" : "draft");
  }

  async function learn() {
    if (!draft?.experiment || !measurement) return;
    setLearningLoading(true);
    setError(null);
    const result = await learnFromExperiment(draft.experiment.id);
    setLearningLoading(false);
    if (!result) { setError("LEARNING FAILED — THE MEASURED RESULT COULD NOT BE LEARNED."); return; }
    setLearning(result);
    const entries = await getGrowthDna();
    if (entries) setGrowthDna(entries);
  }

  async function continueLearning() {
    if (!draft?.experiment) return;
    setContinuing(true);
    setError(null);
    const result = await continueAgentLoop(draft.experiment.id);
    setContinuing(false);
    if (!result) { setError("CONTINUATION FAILED — THE BACKEND DID NOT CONFIRM THE NEXT STEP."); return; }
    setContinuation(result);
    const entries = await getGrowthDna();
    if (entries) setGrowthDna(entries);
  }

  return (
    <section className="intelligence-workspace" aria-labelledby="workspace-title">
      <div className="workspace__top"><div><span className="card__meta">OPPORTUNITY_{opportunity.id.slice(0, 6).toUpperCase()}</span><h2 id="workspace-title">Signal investigation</h2></div><button type="button" className="workspace__close" onClick={onClose} aria-label="Close opportunity workspace">CLOSE ×</button></div>
      <div className="workspace__flow"><span className="is-done">01 OBSERVE ✓</span><span className="is-done">02 DETECT ✓</span><span className={state === "signal" || state === "error" ? "is-active" : "is-done"}>{state === "diagnosing" ? "03 DIAGNOSE ●" : "03 DIAGNOSE ✓"}</span><span className={state === "diagnosed" ? "is-active" : ["simulating", "simulation", "permission", "draft", "approved", "running", "measured"].includes(state) ? "is-done" : ""}>04 STRATEGIZE {state === "diagnosed" ? "●" : ["simulating", "simulation", "permission", "draft", "approved", "running", "measured"].includes(state) ? "✓" : ""}</span><span className={["simulating", "simulation", "permission", "draft", "approved", "running"].includes(state) ? "is-active" : state === "measured" ? "is-done" : ""}>05 EXPERIMENT {["simulating", "simulation", "permission", "draft", "approved", "running"].includes(state) ? "●" : state === "measured" ? "✓" : ""}</span><span className={["running"].includes(state) ? "is-active" : state === "measured" ? "is-done" : ""}>06 MEASURE {state === "running" ? "●" : state === "measured" ? "✓" : ""}</span><span>07 LEARN</span></div>
      <div className="workspace__signal">
        <div className="workspace__signal-copy"><div className="card__top"><span className="card__meta">DETECTION / PERSISTED</span><StatusBadge status={opportunity.status} /></div><div className="workspace__headline"><span>HIGH TRAFFIC</span><span>LOW CONVERSION</span></div><p>Product entity / {opportunity.entity_id}</p></div>
        <div className="workspace__evidence"><span className="intel-label">OBSERVED / EVIDENCE</span><strong>{detail?.evidence.length ?? opportunity.evidence_fact_ids.length}</strong><p>Persisted FactSnapshot references</p></div>
      </div>
      {error && <div className="workspace__error" role="alert">{error}</div>}
      {state === "signal" || state === "error" ? <div className="workspace__action-row"><p>Review the persisted detector evidence before reasoning about possible causes.</p><button type="button" className="diagnose-button" onClick={diagnose}>DIAGNOSE SIGNAL →</button></div> : state === "diagnosing" ? <div className="analyzing-state" role="status"><span className="analyzing-state__mark">◌</span><div><strong>ANALYZING SIGNAL</strong><p>Loading persisted diagnosis and research context...</p></div></div> : state === "diagnosed" ? <div className="workspace__panels"><DiagnosisPanel diagnosis={diagnosis!} /><HypothesisPanel hypotheses={hypotheses} /><StrategyPanel strategies={strategies} onSimulate={simulate} simulatingStrategyId={simulatingStrategyId} /></div> : state === "simulating" ? <div className="analyzing-state" role="status"><span className="analyzing-state__mark">◌</span><div><strong>RUNNING SIMULATION</strong><p>Persisted assumptions are being evaluated by the backend.</p></div></div> : draft ? <div className="phase-stack"><SimulationPanel simulation={draft.simulation} />{state === "simulation" && <button type="button" className="phase-button phase-button--wide" onClick={() => setState("permission")}>CHECK PERMISSION →</button>}{["permission", "draft", "approved", "running", "measured"].includes(state) && <PermissionPanel permission={draft.permission} onContinue={() => setState("draft")} />}{["draft", "approved", "running", "measured"].includes(state) && draft.experiment && <><ExperimentDraftPanel experiment={draft.experiment} /><ExperimentControlPanel experiment={draft.experiment} loading={actionLoading} onAction={experimentAction} error={error} /></>}{state === "measured" && measurement && <><ExperimentResultPanel result={measurement} onLearn={learn} learning={learningLoading} />{learning && <LearningPanel learning={learning} dna={growthDna.find((entry) => entry.id === learning.growth_dna_id) ?? null} continuing={continuing} continuation={continuation} onContinue={continueLearning} />}<GrowthDnaPanel entries={growthDna} /></>}</div> : null}
      <AuditTrailPanel logs={auditLogs} />
    </section>
  );
}