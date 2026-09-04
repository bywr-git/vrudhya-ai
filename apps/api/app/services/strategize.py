"""Deterministic strategy generation.

Strategies describe proposed experiments. They do not execute actions.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hypothesis, Strategy
from app.models.enums import ActionType
from app.services.context import MerchantContext


async def strategize_hypothesis(
    session: AsyncSession,
    ctx: MerchantContext,
    hypothesis_id: UUID,
) -> Strategy:
    """Create an experiment-ready strategy from a hypothesis."""

    hypothesis = (
        await session.execute(
            select(Hypothesis).where(
                Hypothesis.id == hypothesis_id,
                Hypothesis.merchant_id == ctx.merchant_id,
            )
        )
    ).scalar_one_or_none()

    if hypothesis is None:
        raise ValueError("Hypothesis not found")

    strategy = Strategy(
        merchant_id=ctx.merchant_id,
        agent_run_id=hypothesis.agent_run_id,
        hypothesis_id=hypothesis.id,
        action_type=ActionType.synthetic_pdp_copy.value,
        rationale=(
            "Test a controlled product-detail-page copy change because "
            "the observed opportunity is high traffic with low conversion. "
            "The strategy isolates the proposed storefront change while "
            "keeping traffic as the primary input."
        ),
        impact_assumptions={
            "assumption": "Improved PDP messaging may increase purchase conversion",
            "direction": "positive",
            "causal_status": "unproven",
        },
        expected_direction="increase",
        cost="low",
        risk="low",
        implementation_complexity="low",
        primary_metric="product_view_to_purchase_conversion_rate",
        guardrail_metrics=[
            "add_to_cart_rate",
            "checkout_rate",
            "revenue",
        ],
        proposed_change={
            "surface": "product_detail_page",
            "change_type": "copy",
            "control": "existing_product_description",
            "variant": "experiment_generated_product_description",
        },
    )

    session.add(strategy)
    await session.flush()

    return strategy