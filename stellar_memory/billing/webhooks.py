"""Unified webhook handler for all payment providers."""

from __future__ import annotations

import logging

from stellar_memory.auth import AuthManager
from stellar_memory.billing.base import WebhookEvent

logger = logging.getLogger(__name__)


async def handle_subscription_event(
    event: WebhookEvent, auth_mgr: AuthManager
):
    """Process normalized subscription events from any provider."""

    logger.info(
        f"Webhook: {event.provider.value} {event.event_type} "
        f"email={event.customer_email} tier={event.plan_tier}"
    )

    if event.event_type == "subscription_created":
        # Get or create user
        user = await auth_mgr.get_or_create_user(
            event.customer_email, provider=event.provider.value
        )
        # Upgrade tier
        await auth_mgr.update_user_tier(
            email=event.customer_email,
            tier=event.plan_tier,
            provider=event.provider.value,
            provider_subscription_id=event.subscription_id,
        )
        # Log event
        await auth_mgr.log_subscription_event(
            user_id=user.id,
            provider=event.provider.value,
            event_type=event.event_type,
            tier=event.plan_tier,
            raw_data=event.raw_data,
        )
        logger.info(f"User {event.customer_email} upgraded to {event.plan_tier}")

    elif event.event_type == "subscription_updated":
        user = await auth_mgr.get_user_by_email(event.customer_email)
        if user:
            await auth_mgr.update_user_tier(
                email=event.customer_email,
                tier=event.plan_tier,
            )
            await auth_mgr.log_subscription_event(
                user_id=user.id,
                provider=event.provider.value,
                event_type=event.event_type,
                tier=event.plan_tier,
                raw_data=event.raw_data,
            )

    elif event.event_type in ("subscription_cancelled", "subscription_expired"):
        user = await auth_mgr.get_user_by_email(event.customer_email)
        if user:
            # Downgrade to free
            await auth_mgr.update_user_tier(
                email=event.customer_email, tier="free"
            )
            await auth_mgr.log_subscription_event(
                user_id=user.id,
                provider=event.provider.value,
                event_type=event.event_type,
                tier="free",
                raw_data=event.raw_data,
            )
            logger.info(f"User {event.customer_email} downgraded to free")

    elif event.event_type == "payment_success":
        user = await auth_mgr.get_user_by_email(event.customer_email)
        if user:
            await auth_mgr.log_subscription_event(
                user_id=user.id,
                provider=event.provider.value,
                event_type=event.event_type,
                tier=event.plan_tier,
                raw_data=event.raw_data,
            )

    elif event.event_type == "payment_failed":
        user = await auth_mgr.get_user_by_email(event.customer_email)
        if user:
            await auth_mgr.log_subscription_event(
                user_id=user.id,
                provider=event.provider.value,
                event_type=event.event_type,
                tier=event.plan_tier,
                raw_data=event.raw_data,
            )
            logger.warning(
                f"Payment failed for {event.customer_email} "
                f"({event.provider.value})"
            )
