# Vrudhya.ai Data Model

PostgreSQL, UUID primary keys, `created_at` / `updated_at` where rows are mutable. Tenant column `merchant_id` on all merchant-owned tables. Queries must filter `merchant_id` from authenticated context, never from model-supplied input.

## Enumerations

**claim_type:** `observation` | `simulation` | `supported` | `rejected` | `inconclusive`

**opportunity.status:** `open` | `investigating` | `experimenting` | `closed`

**hypothesis.status:** `proposed` | `selected` | `supported` | `rejected` | `inconclusive`

**experiment.status:** `draft` | `awaiting_approval` | `approved` | `rejected_by_merchant` | `running` | `stopped` | `measured`

**permission_outcome:** `allowed` | `approval_required` | `denied`

**dna.kind:** `constraint` | `preference` | `proven_play` | `failed_play` | `baseline` | `asset`

**actor:** `agent` | `merchant` | `system`

**action_type (V1 allowlist):**

- `synthetic_pdp_copy`
- `synthetic_price_test`
- `razorpay_payment_link`
- `razorpay_payment_link_with_offer`
- `razorpay_cancel_payment_link`

Anything else is denied.

## merchants

- `id`
- `name` (Lumi Gifts)
- `data_mode` (`synthetic` | `live_storefront` — V1 uses `synthetic`)
- `autonomy_kill_switch` (boolean, default `false`). When `true`, the merchant kill switch is engaged: no autonomous executes.
- `created_at`

Platform kill switch is configuration, not a row (e.g. `PLATFORM_AUTONOMY_KILL_SWITCH`).

## users / sessions

V1: single operator per demo merchant. `user_id`, `merchant_id`, credential hash. Session supplies `merchant_id` to the API layer.

## products

Synthetic catalog (and later mapped storefront SKUs).

- `id`, `merchant_id`, `sku`, `name`, `price_paise`, `category`, `status`, optional `cost_paise` (margin facts only if populated and trusted)

## events_daily

Storefront grain: `merchant_id`, `product_id` nullable, `day`, `channel`, `variant` (`control` | `variant` | `unassigned`)

Counters: `sessions`, `pdp_views`, `atc`, `checkouts`, `orders`, `revenue_paise`

Source: synthetic storefront (V1). Not Razorpay.

## experiment_assignments

- `experiment_id`, `merchant_id`, `visitor_key` (synthetic), `variant`, `assigned_at`

Used for genuine control/variant experiments on the synthetic storefront.

## payments_raw / orders_raw / payment_links_raw / razorpay_events

JSONB plus extracted `rzp_id`, `status`, `amount`, `method`, `error_code`. Unique on Razorpay id / event id.

These support payment **observations** (success rate, unpaid links). They do not replace `events_daily`.

## fact_snapshots

Immutable.

Columns matching AGENT_SPEC: `fact_id`, `merchant_id`, `metric`, `value`, `unit`, `window`, `method`, `source`, `sample_size`, `computed_at`, optional `product_id`, `experiment_id`.

`source` examples: `bi.storefront`, `bi.razorpay`, `bi.experiment`

Radar and the agent consume this table, not ad hoc queries, for displayed facts.

## opportunities

- `id`, `merchant_id`, `detector_id`, `entity_type`, `entity_id`, `score`, `evidence_fact_ids` (UUID array), `status`, `created_at`

Created only by `detect`. Never by the LLM.

## hypotheses

- fields per AGENT_SPEC
- `agent_run_id`
- `supporting_fact_ids` / `contradicting_fact_ids` must be subset of the run’s pin list (enforced in app)

`supported` / `rejected` updated only by measurement.

## strategies / proposed_changes

Intervention rows: `action_type`, rationale, assumptions JSON (no computed impact), `primary_metric`, `guardrail_metrics`, `proposed_change` JSON (before/after for Preview).

## simulation_results

- `id`, `merchant_id`, `agent_run_id`, `strategy_id`, `assumption_hash`, `outputs` JSON, `claim_type` always `simulation`

## experiments

- `id`, `merchant_id`, `opportunity_id`, `hypothesis_id`, `action_type`, `params` JSON (schema-validated)
- `primary_metric`, `guardrail_metrics`, `window`, `min_sample`
- `status`, `approval_id`
- `control_description`, `variant_description`

## experiment_observations

Daily or per-variant metrics from the synthetic storefront and, separately, payment metrics from Razorpay with `source` distinguished.

`claim_type` = `observation` until measurement closes the experiment.

## experiment_results

Written once at measurement:

- `claim_type`: `supported` | `rejected` | `inconclusive`
- `primary_delta`, `guardrail_breaches`, `method`, `notes`

Unmeasured `stopped` experiments do not insert `proven_play` or `failed_play`. Optional result row with `inconclusive` is allowed.

## agent_runs

- `id`, `merchant_id` (from auth at insert)
- `opportunity_id`
- `pinned_fact_ids` (UUID array, append-only during the run)
- `state` (includes `awaiting_approval`)
- `created_at`

## agent_messages / tool_calls

Trace for eval. Tool args must not contain `merchant_id`.

## permission_policies

One row per merchant: JSON policy (`allow_action_types`, autonomy map, limits). Cannot whitelist denied V1 actions.

## growth_dna

- `kind`, `key`, `body`, `evidence_experiment_id` (required for plays)
- `active`

Plays require a measured `experiment_results` row. Constraints/preferences: `actor=merchant`.

## audit_log

Append-only. No UPDATE/DELETE in application roles.

Columns per AGENT_SPEC §17.

## jobs

Queue: `observe`, `detect`, `experiment_tick`, `razorpay_sync`, `agent_continue`. `job_key` unique for idempotency.

## Seed: Lumi Gifts

At least one SKU with high `pdp_views`, low conversion, and sample size above detector thresholds, so Radar can fire without the LLM.
