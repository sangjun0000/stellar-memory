"""Stripe payment provider."""

from __future__ import annotations

import logging

from .base import (
    BillingProvider,
    CheckoutResult,
    PaymentProvider,
    WebhookEvent,
)

logger = logging.getLogger(__name__)

# Stripe event → normalized event type mapping
_EVENT_MAP = {
    "checkout.session.completed": "subscription_created",
    "invoice.paid": "payment_success",
    "invoice.payment_failed": "payment_failed",
    "customer.subscription.updated": "subscription_updated",
    "customer.subscription.deleted": "subscription_expired",
}


class StripeProvider(BillingProvider):
    """Stripe integration (global alternative, direct payment processing)."""

    def __init__(
        self,
        secret_key: str,
        webhook_secret: str,
        price_pro: str,
        price_team: str,
    ):
        try:
            import stripe
        except ImportError:
            raise ImportError(
                "stripe package required. Install with: pip install stripe"
            )
        stripe.api_key = secret_key
        self._stripe = stripe
        self._webhook_secret = webhook_secret
        self._prices = {"pro": price_pro, "team": price_team}

    async def create_checkout(
        self, tier, customer_email, success_url, cancel_url
    ) -> CheckoutResult:
        price_id = self._prices.get(tier)
        if not price_id:
            raise ValueError(f"Unknown tier: {tier}")

        session = self._stripe.checkout.Session.create(
            mode="subscription",
            customer_email=customer_email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"tier": tier},
        )
        return CheckoutResult(
            checkout_url=session.url,
            provider=PaymentProvider.STRIPE,
            session_id=session.id,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        event = self._stripe.Webhook.construct_event(
            payload, signature, self._webhook_secret
        )

        event_type = event["type"]
        data_obj = event["data"]["object"]

        # Extract email and tier based on event type
        email = ""
        tier = "pro"
        sub_id = ""

        if event_type == "checkout.session.completed":
            email = data_obj.get("customer_email", "")
            tier = data_obj.get("metadata", {}).get("tier", "pro")
            sub_id = data_obj.get("subscription", "")
        elif event_type in ("invoice.paid", "invoice.payment_failed"):
            email = data_obj.get("customer_email", "")
            sub_id = data_obj.get("subscription", "")
            # Tier from subscription metadata
            lines = data_obj.get("lines", {}).get("data", [])
            if lines:
                tier = lines[0].get("metadata", {}).get("tier", "pro")
        elif event_type in (
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            sub_id = data_obj.get("id", "")
            tier = data_obj.get("metadata", {}).get("tier", "pro")

        return WebhookEvent(
            provider=PaymentProvider.STRIPE,
            event_type=_EVENT_MAP.get(event_type, event_type),
            customer_email=email,
            plan_tier=tier,
            subscription_id=sub_id,
            raw_data=dict(event),
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        self._stripe.Subscription.modify(
            subscription_id, cancel_at_period_end=True
        )
        return True

    async def get_portal_url(self, customer_id: str) -> str:
        session = self._stripe.billing_portal.Session.create(
            customer=customer_id
        )
        return session.url
