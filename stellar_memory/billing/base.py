"""Payment provider abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class PaymentProvider(str, Enum):
    LEMONSQUEEZY = "lemonsqueezy"
    STRIPE = "stripe"
    TOSS = "toss"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


@dataclass
class CheckoutResult:
    checkout_url: str
    provider: PaymentProvider
    session_id: str | None = None
    client_key: str | None = None  # For TossPayments frontend SDK


@dataclass
class WebhookEvent:
    provider: PaymentProvider
    event_type: str  # normalized: subscription_created, payment_success, etc.
    customer_email: str
    plan_tier: str  # "pro" | "team"
    subscription_id: str
    raw_data: dict = field(default_factory=dict)


class BillingProvider(ABC):
    """Abstract base class for payment providers."""

    @abstractmethod
    async def create_checkout(
        self,
        tier: str,
        customer_email: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutResult:
        ...

    @abstractmethod
    async def verify_webhook(
        self, payload: bytes, signature: str
    ) -> WebhookEvent:
        ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        ...

    @abstractmethod
    async def get_portal_url(self, customer_id: str) -> str:
        ...
