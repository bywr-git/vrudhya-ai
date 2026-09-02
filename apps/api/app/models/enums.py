"""Domain enumerations matching docs/DATA_MODEL.md."""

from enum import StrEnum


class ClaimType(StrEnum):
    observation = "observation"
    simulation = "simulation"
    supported = "supported"
    rejected = "rejected"
    inconclusive = "inconclusive"


class DataMode(StrEnum):
    synthetic = "synthetic"
    live_storefront = "live_storefront"


class OpportunityStatus(StrEnum):
    open = "open"
    investigating = "investigating"
    experimenting = "experimenting"
    closed = "closed"


class HypothesisStatus(StrEnum):
    proposed = "proposed"
    selected = "selected"
    supported = "supported"
    rejected = "rejected"
    inconclusive = "inconclusive"


class ExperimentStatus(StrEnum):
    draft = "draft"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    rejected_by_merchant = "rejected_by_merchant"
    running = "running"
    stopped = "stopped"
    measured = "measured"


class PermissionOutcome(StrEnum):
    allowed = "allowed"
    approval_required = "approval_required"
    denied = "denied"


class DnaKind(StrEnum):
    constraint = "constraint"
    preference = "preference"
    proven_play = "proven_play"
    failed_play = "failed_play"
    baseline = "baseline"
    asset = "asset"


class Actor(StrEnum):
    agent = "agent"
    merchant = "merchant"
    system = "system"


class ActionType(StrEnum):
    synthetic_pdp_copy = "synthetic_pdp_copy"
    synthetic_price_test = "synthetic_price_test"
    razorpay_payment_link = "razorpay_payment_link"
    razorpay_payment_link_with_offer = "razorpay_payment_link_with_offer"
    razorpay_cancel_payment_link = "razorpay_cancel_payment_link"


class EventType(StrEnum):
    session = "session"
    product_view = "product_view"
    add_to_cart = "add_to_cart"
    checkout_started = "checkout_started"
    purchase = "purchase"
    payment_success = "payment_success"
    payment_failed = "payment_failed"


class ProductStatus(StrEnum):
    active = "active"
    archived = "archived"


class OrderStatus(StrEnum):
    placed = "placed"
    paid = "paid"
    cancelled = "cancelled"
    failed = "failed"


class PaymentStatus(StrEnum):
    success = "success"
    failed = "failed"


class ExperimentVariant(StrEnum):
    control = "control"
    variant = "variant"
    unassigned = "unassigned"


class AgentRunState(StrEnum):
    created = "created"
    running = "running"
    awaiting_approval = "awaiting_approval"
    completed = "completed"
    failed = "failed"


class JobType(StrEnum):
    observe = "observe"
    detect = "detect"
    experiment_tick = "experiment_tick"
    razorpay_sync = "razorpay_sync"
    agent_continue = "agent_continue"


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
