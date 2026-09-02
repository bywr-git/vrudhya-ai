# Vrudhya.ai — Product Specification

## Product

Vrudhya.ai

## Tagline

Find what grows. Prove what works.

## Core Problem

Merchants often know their revenue is changing, but do not know:

- where revenue is being lost
- why it is happening
- which intervention is most likely to help
- whether the intervention actually worked

Existing analytics tools primarily show what happened.

Vrudhya aims to determine what should be tested next and measure the result.

## Core Promise

Vrudhya discovers revenue opportunities, diagnoses likely causes, generates testable growth hypotheses, recommends interventions, executes permitted actions, measures outcomes, and learns what works for the individual merchant.

Discovery of opportunities is performed by a deterministic detection engine. The AI agent investigates those opportunities. It is not the source of Opportunity Radar facts.

## Primary User

Small and medium-sized online merchants.

## Primary Objective

Maximize sustainable incremental profit when reliable margin facts exist.

Otherwise optimize incremental revenue with mandatory margin and risk guardrails.

Vrudhya must not optimize revenue in a way that violates those guardrails or merchant-defined constraints.

## Claim Types

Every quantitative or causal statement shown to the merchant must be labelled as exactly one of:

| Label | Meaning |
| --- | --- |
| `observation` | A deterministic fact or measured metric. No causal claim. |
| `simulation` | Output of the simulation engine. Not proof of what happened or will happen. |
| `supported` | A hypothesis supported by a measured experiment that met pre-registered criteria. |
| `rejected` | A hypothesis rejected by a measured experiment that met pre-registered criteria. |
| `inconclusive` | Insufficient evidence, an unmeasured stop, or a result that does not meet support or reject criteria. |

The product must never present a `simulation` or a hypothesis as an `observation`, `supported`, or `rejected` result.

## Core Loop

Observe
→ Detect
→ Diagnose
→ Hypothesize
→ Strategize
→ Simulate
→ Permission check (always)
→ Execute or wait for merchant approval
→ Measure
→ Learn
→ Repeat

There is no optional permission gate. Every write action is evaluated by the deterministic permission engine before it runs.

If the outcome is `approval_required`, the loop waits. It does not execute.

If the global or merchant autonomous-action kill switch is on, no action may execute autonomously.

## Constraints

Vrudhya must:

- explain recommendations
- distinguish facts from hypotheses
- avoid unsupported claims
- label every claim with a claim type
- respect merchant permissions
- deny unauthorized financial actions
- record write actions in an audit trail
- measure experiment outcomes with a pre-registered design
- acknowledge uncertainty
- learn from **measured** failed experiments as `failed_play`
- not turn unmeasured failures into Growth DNA plays

## Core Product Areas

1. Opportunity Radar — detector output only; facts from the BI layer
2. AI Diagnosis — facts vs hypotheses, citing pinned FactSnapshots
3. Hypothesis Engine
4. Strategy Generator
5. Growth Preview — simulations only, labelled as such
6. Experiment Lab — control/variant experiments on the synthetic storefront in V1
7. Revenue Impact — measured observations and, when criteria are met, supported or rejected incrementality
8. Growth DNA
9. Agent Permissions — including the autonomous-action kill switch
10. Agent Audit Trail

## Opportunity Radar

The detection engine, not the LLM, creates opportunities.

Radar may only display:

- opportunities persisted by the detection engine
- FactSnapshots that constitute their evidence

The LLM must never be the source of Opportunity Radar facts or opportunity rows.

## Experiments (V1)

V1 uses a **synthetic storefront** as the assignment and storefront-analytics layer. Genuine control and variant assignment happens there (session or visitor assignment, PDP and checkout funnel events).

**Razorpay** is the payment execution and payment-measurement layer. It is not the storefront analytics layer. Traffic, PDP conversion, and catalog funnels do not come from Razorpay APIs.

V1 Razorpay is **Test Mode only**.

Payment-related writes require explicit merchant approval. They are never autonomous in V1.

Refunds, captures, live-mode actions, and arbitrary HTTP are denied in V1.

## Growth DNA

Persistent memory may be created only from:

- measured experiment outcomes
- merchant-authored constraints
- merchant-authored preferences

Failed **measured** experiments create `failed_play`.

Unmeasured failures (tool errors, cancelled runs, stopped before measurement) do not become `proven_play` or `failed_play`.

## Tenant Isolation

Each merchant’s data is isolated.

`merchant_id` comes only from the authenticated session. The product must not accept a merchant identifier from the agent, from tool arguments supplied by the model, or from client-provided IDs that are not bound to that session.

## Initial Merchant

Use a synthetic demo merchant for development.

Merchant name: Lumi Gifts

Category: Gifting / D2C

The system must be designed so the demo merchant can later be replaced by real merchant data without changing the growth loop. Storefront analytics remain behind a storefront adapter. Payments remain behind a payments adapter.

## Initial Success Scenario

The detection engine identifies a product with:

- high traffic
- low conversion
- sufficient supporting evidence

Those traits are FactSnapshots on the opportunity. They are not inferred by the LLM.

The agent then:

1. investigates the detected opportunity using pinned FactSnapshots
2. forms multiple hypotheses (not facts)
3. recommends interventions
4. explains the recommendation
5. shows the proposed change and a labelled simulation
6. submits the write through the permission engine
7. waits for merchant approval when required (always for Razorpay writes in V1)
8. executes only if permitted
9. measures the outcome on the synthetic storefront (and payment metrics from Razorpay when relevant)
10. records the result as observation, supported, rejected, or inconclusive
11. updates Growth DNA only when the outcome was measured, or when the merchant authors a constraint or preference
