"""TossPayments provider (Korean domestic payments)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import uuid

import httpx

from .base import (
    BillingProvider,
    CheckoutResult,
    PaymentProvider,
    WebhookEvent,
)

logger = logging.getLogger(__name__)

TOSS_API = "https://api.tosspayments.com/v1"

# Toss prices in KRW
TOSS_PRICES = {
    "pro": 39_000,
    "team": 129_000,
}


class TossProvider(BillingProvider):
    """TossPayments integration (Korean domestic, billing key for recurring)."""

    def __init__(
        self,
        secret_key: str,
        client_key: str,
        webhook_secret: str,
    ):
        self._secret_key = secret_key
        self._client_key = client_key
        self._webhook_secret = webhook_secret
        self._auth = base64.b64encode(
            f"{secret_key}:".encode()
        ).decode()

    async def create_checkout(
        self, tier, customer_email, success_url, cancel_url
    ) -> CheckoutResult:
        # TossPayments uses frontend SDK for payment window
        # Backend generates customerKey and returns client_key for SDK init
        customer_key = str(uuid.uuid4())
        return CheckoutResult(
            checkout_url="",  # Toss uses JS SDK, no direct URL
            provider=PaymentProvider.TOSS,
            session_id=customer_key,
            client_key=self._client_key,
        )

    async def issue_billing_key(
        self, customer_key: str, auth_key: str
    ) -> str:
        """Issue billing key after frontend SDK auth completes."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TOSS_API}/billing/authorizations/issue",
                json={
                    "customerKey": customer_key,
                    "authKey": auth_key,
                },
                headers={"Authorization": f"Basic {self._auth}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["billingKey"]

    async def charge_billing(
        self,
        billing_key: str,
        customer_key: str,
        amount: int,
        order_id: str,
        order_name: str,
    ) -> dict:
        """Execute recurring charge with billing key."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TOSS_API}/billing/{billing_key}",
                json={
                    "customerKey": customer_key,
                    "amount": amount,
                    "orderId": order_id,
                    "orderName": order_name,
                },
                headers={"Authorization": f"Basic {self._auth}"},
            )
            resp.raise_for_status()
            return resp.json()

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        # Toss webhook signature verification
        digest = hmac.new(
            self._webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid TossPayments webhook signature")

        body = json.loads(payload)
        event_type = body.get("eventType", "")
        data = body.get("data", {})

        # Map Toss events to normalized types
        normalized = event_type
        if event_type == "PAYMENT_STATUS_CHANGED":
            status = data.get("status", "")
            if status == "DONE":
                normalized = "payment_success"
            elif status == "CANCELED":
                normalized = "subscription_cancelled"
            elif status == "ABORTED":
                normalized = "payment_failed"

        # Extract tier from orderId pattern: stellar-{tier}-{userId}-{YYYYMM}
        order_id = data.get("orderId", "")
        tier = "pro"
        parts = order_id.split("-")
        if len(parts) >= 2 and parts[1] in ("pro", "team"):
            tier = parts[1]

        return WebhookEvent(
            provider=PaymentProvider.TOSS,
            event_type=normalized,
            customer_email=data.get("customerEmail", ""),
            plan_tier=tier,
            subscription_id=data.get("billingKey", order_id),
            raw_data=body,
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        # Toss billing key based: we manage subscriptions ourselves
        # Just mark as cancelled in our DB; stop cron charges
        logger.info(f"Toss subscription cancelled: {subscription_id}")
        return True

    async def get_portal_url(self, customer_id: str) -> str:
        # Toss has no customer portal; return our own billing page
        return f"https://stellar-memory.com/billing?customer={customer_id}"
