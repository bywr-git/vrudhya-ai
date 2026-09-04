"""Deterministic permission decisions. No action is executed here."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PermissionPolicy, Strategy
from app.models.enums import ActionType, PermissionOutcome
from app.services.context import MerchantContext


@dataclass(frozen=True)
class PermissionDecision:
    merchant_id: UUID
    strategy_id: UUID
    action_type: str
    outcome: str
    reason: str


async def check_strategy_permission(
    session: AsyncSession,
    ctx: MerchantContext,
    strategy_id: UUID,
) -> PermissionDecision:
    strategy = (await session.execute(select(Strategy).where(
        Strategy.id == strategy_id, Strategy.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if strategy is None:
        raise ValueError("Strategy not found")

    action_type = strategy.action_type
    allowed_actions = {action.value for action in ActionType}
    if action_type not in allowed_actions:
        return PermissionDecision(ctx.merchant_id, strategy.id, action_type,
                                  PermissionOutcome.denied.value, "Action type is not allowlisted")
    if action_type.startswith("razorpay_"):
        return PermissionDecision(ctx.merchant_id, strategy.id, action_type,
                                  PermissionOutcome.approval_required.value,
                                  "Payment-related writes require explicit merchant approval")

    policy = (await session.execute(select(PermissionPolicy).where(
        PermissionPolicy.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    policy_body = policy.policy if policy is not None else {}
    autonomous_actions = set(policy_body.get("autonomous_action_types", []))
    if ctx.autonomy_kill_switch:
        return PermissionDecision(ctx.merchant_id, strategy.id, action_type,
                                  PermissionOutcome.approval_required.value,
                                  "Merchant autonomy kill switch is enabled")
    if action_type in autonomous_actions:
        return PermissionDecision(ctx.merchant_id, strategy.id, action_type,
                                  PermissionOutcome.allowed.value, "Action is explicitly allowed autonomously")
    if policy is not None and action_type not in set(policy_body.get("allow_action_types", [])):
        return PermissionDecision(ctx.merchant_id, strategy.id, action_type,
                                  PermissionOutcome.denied.value, "Action type is not allowed by merchant policy")
    return PermissionDecision(ctx.merchant_id, strategy.id, action_type,
                              PermissionOutcome.approval_required.value,
                              "Merchant approval is required by default")