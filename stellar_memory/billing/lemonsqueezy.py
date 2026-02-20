"""Lemon Squeezy payment provider (Merchant of Record)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

import httpx

from .base import (
    BillingProvider,
    CheckoutResult,
    PaymentProvider,
    WebhookEvent,
)

logger = logging.getLogger(__name__)

LEMON_API = "https://api.lemonsqueezy.com/v1"

# Lemon Squeezy event → normalized event type mapping
_EVENT_MAP = {
    "subscription_created": "subscription_created",
    "subscription_updated": "subscription_updated",
    "subscription_cancelled": "subscription_cancelled",
    "subscription_expired": "subscription_expired",
    "subscription_payment_success": "payment_success",
    "subscription_payment_failed": "payment_failed",
}


class LemonSqueezyProvider(BillingProvider):
    """Lemon Squeezy integration (global default, MoR handles VAT/tax)."""

    def __init__(
        self,
        api_key: str,
        store_id: str,
        variant_pro: str,
        variant_team: str,
        webhook_secret: str,
    ):
        self._api_key = api_key
        self._store_id = store_id
        self._variants = {"pro": variant_pro, "team": variant_team}
        self._webhook_secret = webhook_secret

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }

    async def create_checkout(
        self, tier, customer_email, success_url, cancel_url
    ) -> CheckoutResult:
        variant_id = self._variants.get(tier)
        if not variant_id:
            raise ValueError(f"Unknown tier: {tier}")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LEMON_API}/checkouts",
                json={
                    "data": {
                        "type": "checkouts",
                        "attributes": {
                            "checkout_data": {
                                "email": customer_email,
                                "custom": {"tier": tier},
                            },
                            "product_options": {"redirect_url": success_url},
                        },
                        "relationships": {
                            "store": {
                                "data": {
                                    "type": "stores",
                                    "id": self._store_id,
                                }
                            },
                            "variant": {
                                "data": {
                                    "type": "variants",
                                    "id": variant_id,
                                }
                            },
                        },
                    }
                },
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return CheckoutResult(
                checkout_url=data["data"]["attributes"]["url"],
                provider=PaymentProvider.LEMONSQUEEZY,
                session_id=data["data"]["id"],
            )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        digest = hmac.new(
            self._webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid Lemon Squeezy webhook signature")

        body = json.loads(payload)
        meta = body.get("meta", {})
        event_name = meta.get("event_name", "")
        attrs = body.get("data", {}).get("attributes", {})

        # Extract tier from custom data or variant
        custom = meta.get("custom_data", {})
        tier = custom.get("tier", "pro")

        # Extract email
        email = attrs.get("user_email", "")

        # Subscription ID
        sub_id = str(body.get("data", {}).get("id", ""))

        return WebhookEvent(
            provider=PaymentProvider.LEMONSQUEEZY,
            event_type=_EVENT_MAP.get(event_name, event_name),
            customer_email=email,
            plan_tier=tier,
            subscription_id=sub_id,
            raw_data=body,
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{LEMON_API}/subscriptions/{subscription_id}",
                headers=self._headers(),
            )
            return resp.status_code == 200

    async def get_portal_url(self, customer_id: str) -> str:
        # Lemon Squeezy provides urls.update_payment_method per subscription
        # We return the customer portal URL
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LEMON_API}/subscriptions/{customer_id}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                urls = data["data"]["attributes"].get("urls", {})
                return urls.get(
                    "customer_portal",
                    urls.get("update_payment_method", ""),
                )
        return ""
