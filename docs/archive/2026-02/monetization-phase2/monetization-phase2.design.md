# Design: Monetization Phase 2

> **Feature**: monetization-phase2
> **Plan Reference**: `docs/01-plan/features/monetization-phase2.plan.md`
> **Created**: 2026-02-18
> **Status**: Draft

---

## 1. Architecture Overview

```
Browser (stellar-memory.com)
  │
  ├── "Subscribe Pro" 클릭
  │     └── 결제 수단 선택 모달
  │           ├── Lemon Squeezy (글로벌, 기본)
  │           ├── Stripe (글로벌, 대안)
  │           └── 토스페이먼츠 (한국)
  │
  ├── Lemon Squeezy ─── Checkout Overlay ─── Webhook ──┐
  ├── Stripe ────────── Checkout Session ── Webhook ──┤
  ├── TossPayments ──── 결제창 SDK ──────── Webhook ──┤
  │                                                    │
  └── api.stellar-memory.com (Fly.io)  ◄──────────────┘
        ├── /webhook/lemonsqueezy   (Webhook 수신)
        ├── /webhook/stripe         (Webhook 수신)
        ├── /webhook/toss           (Webhook 수신)
        │
        ├── /auth/register          (사용자 등록)
        ├── /auth/api-keys          (API Key 관리)
        ├── /auth/usage             (사용량 조회)
        ├── /billing/portal         (구독 관리 포털)
        │
        ├── /api/v1/store           (기존 API + tier 제한)
        ├── /api/v1/recall          ...
        │
        └── Neon PostgreSQL (pgvector)
              ├── users
              ├── api_keys
              ├── subscriptions
              └── memories (기존)
```

---

## 2. F1: 결제 시스템 설계

### 2.1 결제 Provider 비교

| | Lemon Squeezy | Stripe | 토스페이먼츠 |
|---|---|---|---|
| **역할** | MoR (세금 대행) | 직접 결제 | 국내 결제 |
| **수수료** | 5% + $0.50 | 2.9% + $0.30 | 3.4% (카드) |
| **VAT/세금** | 자동 처리 | 직접 처리 | 해당 없음 |
| **구독 관리** | 내장 | 내장 | 빌링키 직접 관리 |
| **통화** | USD 기본 | 다통화 | KRW 전용 |
| **인증** | Bearer API Key | Basic (secret) | Basic (secret:) |
| **Python SDK** | lemonsqueezy-py-api | stripe | python-tosspayments |

### 2.2 가격 체계

| Tier | Lemon Squeezy (USD) | Stripe (USD) | 토스페이먼츠 (KRW) |
|------|:---:|:---:|:---:|
| Free | $0 | $0 | ₩0 |
| Pro | $29/mo | $29/mo | ₩39,000/월 |
| Team | $99/mo | $99/mo | ₩129,000/월 |

### 2.3 PaymentProvider 추상화

```python
# stellar_memory/billing/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    client_key: str | None = None  # TossPayments frontend SDK용

@dataclass
class WebhookEvent:
    provider: PaymentProvider
    event_type: str          # normalized: subscription_created, payment_success, etc.
    customer_email: str
    plan_tier: str           # "pro" | "team"
    subscription_id: str
    raw_data: dict = field(default_factory=dict)

class BillingProvider(ABC):
    @abstractmethod
    async def create_checkout(self, tier: str, customer_email: str,
                              success_url: str, cancel_url: str) -> CheckoutResult:
        ...

    @abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        ...

    @abstractmethod
    async def get_portal_url(self, customer_id: str) -> str:
        ...
```

### 2.4 Lemon Squeezy 연동

```python
# stellar_memory/billing/lemonsqueezy.py

import httpx
from .base import BillingProvider, CheckoutResult, WebhookEvent, PaymentProvider

LEMON_API = "https://api.lemonsqueezy.com/v1"

class LemonSqueezyProvider(BillingProvider):
    def __init__(self, api_key: str, store_id: str,
                 variant_pro: str, variant_team: str,
                 webhook_secret: str):
        self._api_key = api_key
        self._store_id = store_id
        self._variants = {"pro": variant_pro, "team": variant_team}
        self._webhook_secret = webhook_secret

    async def create_checkout(self, tier, customer_email, success_url, cancel_url):
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{LEMON_API}/checkouts", json={
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "email": customer_email,
                            "custom": {"tier": tier}
                        },
                        "product_options": {"redirect_url": success_url}
                    },
                    "relationships": {
                        "store": {"data": {"type": "stores", "id": self._store_id}},
                        "variant": {"data": {"type": "variants", "id": self._variants[tier]}}
                    }
                }
            }, headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            })
            data = resp.json()
            return CheckoutResult(
                checkout_url=data["data"]["attributes"]["url"],
                provider=PaymentProvider.LEMONSQUEEZY,
                session_id=data["data"]["id"],
            )

    async def verify_webhook(self, payload, signature):
        import hmac, hashlib
        digest = hmac.new(
            self._webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid webhook signature")
        # Parse and normalize event
        ...

    async def cancel_subscription(self, subscription_id):
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{LEMON_API}/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            return resp.status_code == 200

    async def get_portal_url(self, customer_id):
        # Lemon Squeezy provides urls.update_payment_method per subscription
        ...
```

**Lemon Squeezy Webhook Events:**
| Event | 용도 |
|-------|------|
| `subscription_created` | 구독 시작 → 사용자 생성 + API Key 발급 |
| `subscription_updated` | 플랜 변경 → tier 업데이트 |
| `subscription_cancelled` | 취소 → grace period 시작 |
| `subscription_expired` | 만료 → tier를 free로 다운그레이드 |
| `subscription_payment_success` | 결제 성공 → 갱신 확인 |
| `subscription_payment_failed` | 결제 실패 → 알림 |

### 2.5 Stripe 연동

```python
# stellar_memory/billing/stripe_provider.py

import stripe
from .base import BillingProvider, CheckoutResult, WebhookEvent, PaymentProvider

class StripeProvider(BillingProvider):
    def __init__(self, secret_key: str, webhook_secret: str,
                 price_pro: str, price_team: str):
        stripe.api_key = secret_key
        self._webhook_secret = webhook_secret
        self._prices = {"pro": price_pro, "team": price_team}

    async def create_checkout(self, tier, customer_email, success_url, cancel_url):
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=customer_email,
            line_items=[{"price": self._prices[tier], "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"tier": tier},
        )
        return CheckoutResult(
            checkout_url=session.url,
            provider=PaymentProvider.STRIPE,
            session_id=session.id,
        )

    async def verify_webhook(self, payload, signature):
        event = stripe.Webhook.construct_event(
            payload, signature, self._webhook_secret
        )
        # Normalize to WebhookEvent
        ...

    async def cancel_subscription(self, subscription_id):
        stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        return True

    async def get_portal_url(self, customer_id):
        session = stripe.billing_portal.Session.create(customer=customer_id)
        return session.url
```

**Stripe Webhook Events:**
| Event | 용도 |
|-------|------|
| `checkout.session.completed` | 결제 완료 → 사용자 생성 + API Key |
| `invoice.paid` | 갱신 성공 → 구독 연장 |
| `invoice.payment_failed` | 결제 실패 → 알림 |
| `customer.subscription.updated` | 플랜 변경 → tier 업데이트 |
| `customer.subscription.deleted` | 구독 삭제 → free 다운그레이드 |

### 2.6 토스페이먼츠 연동

```python
# stellar_memory/billing/toss_provider.py

import httpx, base64
from .base import BillingProvider, CheckoutResult, WebhookEvent, PaymentProvider

TOSS_API = "https://api.tosspayments.com/v1"

class TossProvider(BillingProvider):
    def __init__(self, secret_key: str, webhook_secret: str,
                 client_key: str):
        self._secret_key = secret_key
        self._webhook_secret = webhook_secret
        self._client_key = client_key  # 프론트엔드 결제창용
        self._auth = base64.b64encode(
            f"{secret_key}:".encode()
        ).decode()

    async def create_checkout(self, tier, customer_email, success_url, cancel_url):
        # 토스는 프론트엔드 SDK로 결제창을 띄우는 방식
        # 백엔드에서는 customerKey 생성 후 프론트에 전달
        import uuid
        customer_key = str(uuid.uuid4())
        return CheckoutResult(
            checkout_url="",  # 토스는 JS SDK로 결제창 호출
            provider=PaymentProvider.TOSS,
            session_id=customer_key,
        )

    async def issue_billing_key(self, customer_key: str,
                                 auth_key: str) -> str:
        """빌링키 발급 (결제창에서 인증 후 호출)"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TOSS_API}/billing/authorizations/issue",
                json={"customerKey": customer_key, "authKey": auth_key},
                headers={"Authorization": f"Basic {self._auth}"},
            )
            data = resp.json()
            return data["billingKey"]

    async def charge_billing(self, billing_key: str, customer_key: str,
                              amount: int, order_id: str, order_name: str):
        """빌링키로 자동결제 실행"""
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
            return resp.json()

    async def verify_webhook(self, payload, signature):
        # 토스 웹훅 시그니처 검증
        ...

    async def cancel_subscription(self, subscription_id):
        # 빌링키 기반이므로 자체 구독 관리에서 중지
        ...

    async def get_portal_url(self, customer_id):
        # 토스는 자체 포털이 없으므로 우리 관리 페이지 URL 반환
        return f"https://stellar-memory.com/billing?customer={customer_id}"
```

**토스 결제 흐름 (빌링키 방식):**
```
1. 프론트: TossPayments SDK 로드 → requestBillingAuth() 호출
2. 토스: 결제창 표시 → 카드 정보 입력 → 인증
3. 프론트: successUrl로 리다이렉트 (authKey 포함)
4. 백엔드: POST /billing/toss/confirm → issue_billing_key(authKey)
5. 백엔드: billingKey 저장 → 매월 charge_billing() 크론 실행
```

**토스 가격 (KRW):**
| Tier | 월 금액 | orderId 형식 |
|------|:-------:|-------------|
| Pro | ₩39,000 | `stellar-pro-{userId}-{YYYYMM}` |
| Team | ₩129,000 | `stellar-team-{userId}-{YYYYMM}` |

---

## 3. F2: 사용자 계정 & API Key 설계

### 3.1 DB 스키마

```sql
-- users 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(20) NOT NULL DEFAULT 'free',  -- free/pro/team
    provider VARCHAR(20),                       -- lemonsqueezy/stripe/toss
    provider_customer_id VARCHAR(255),          -- 외부 고객 ID
    provider_subscription_id VARCHAR(255),      -- 외부 구독 ID
    billing_key VARCHAR(255),                   -- 토스 빌링키 (암호화)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- api_keys 테이블
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,              -- SHA-256 해시
    key_prefix VARCHAR(20) NOT NULL,            -- sk-stellar-xxxx... (표시용)
    name VARCHAR(100) DEFAULT 'Default',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- subscriptions 히스토리
CREATE TABLE subscription_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,            -- created/renewed/cancelled/expired
    tier VARCHAR(20) NOT NULL,
    amount_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = TRUE;
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_subscription_events_user ON subscription_events(user_id);
```

### 3.2 API Key 형식

```
sk-stellar-{random_32_chars}

예시: sk-stellar-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

- **생성**: `secrets.token_hex(16)` → 32 hex chars
- **저장**: SHA-256 해시만 DB에 저장 (원문 저장 안 함)
- **표시**: `sk-stellar-a1b2...` (prefix만 노출)
- **발급 시**: 한 번만 전체 키 표시 (이후 조회 불가)

### 3.3 인증 미들웨어 리팩토링

```python
# stellar_memory/auth.py

import hashlib
from fastapi import Request, HTTPException

async def authenticate_api_key(request: Request) -> dict:
    """API Key 인증 → 사용자 + tier 정보 반환"""
    key = request.headers.get("X-API-Key") or ""
    if not key:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            key = auth[7:]
    if not key:
        raise HTTPException(401, "API key required")

    key_hash = hashlib.sha256(key.encode()).hexdigest()
    # DB에서 key_hash로 조회 → user + tier
    user = await get_user_by_api_key(key_hash)
    if not user:
        raise HTTPException(401, "Invalid API key")

    return {"user_id": user.id, "tier": user.tier, "email": user.email}
```

### 3.4 Auth API 엔드포인트

```python
# POST /auth/register
# Body: {"email": "user@example.com"}
# Response: {"user_id": "uuid", "api_key": "sk-stellar-xxxxx...", "tier": "free"}
# Note: API Key는 이 응답에서만 전체 노출

# GET /auth/api-keys
# Headers: X-API-Key: sk-stellar-xxxxx
# Response: {"keys": [{"id": "uuid", "prefix": "sk-stellar-a1b2", "name": "Default", "created_at": "..."}]}

# POST /auth/api-keys
# Headers: X-API-Key: sk-stellar-xxxxx
# Body: {"name": "Production"}
# Response: {"api_key": "sk-stellar-new-key...", "id": "uuid"}

# DELETE /auth/api-keys/{key_id}
# Headers: X-API-Key: sk-stellar-xxxxx
# Response: {"deleted": true}
```

---

## 4. F3: Tier 기반 제한

### 4.1 Tier 설정

```python
# stellar_memory/billing/tiers.py

TIER_LIMITS = {
    "free": {
        "max_memories": 5_000,
        "max_agents": 1,
        "rate_limit": 60,       # per minute
        "max_api_keys": 1,
    },
    "pro": {
        "max_memories": 50_000,
        "max_agents": 5,
        "rate_limit": 300,
        "max_api_keys": 5,
    },
    "team": {
        "max_memories": 500_000,
        "max_agents": 20,
        "rate_limit": 1_000,
        "max_api_keys": 20,
    },
}
```

### 4.2 Enforcement 미들웨어

```python
async def check_tier_limits(request: Request, user: dict):
    tier = user["tier"]
    limits = TIER_LIMITS[tier]

    # Rate limit (tier별)
    check_rate_limit(request, limits["rate_limit"])

    # Memory count limit (store 엔드포인트만)
    if request.url.path.endswith("/store"):
        count = await get_memory_count(user["user_id"])
        if count >= limits["max_memories"]:
            raise HTTPException(
                403,
                f"Memory limit reached ({count}/{limits['max_memories']}). "
                f"Upgrade to {next_tier(tier)} for more."
            )
```

---

## 5. F4: Cloud 배포

### 5.1 Fly.io 설정 (fly.toml)

```toml
app = "stellar-memory-api"
primary_region = "nrt"  # Tokyo (한국에서 가장 가까운 리전)

[build]
  dockerfile = "Dockerfile"

[env]
  STELLAR_STORAGE_BACKEND = "postgresql"
  STELLAR_HOST = "0.0.0.0"
  STELLAR_PORT = "8080"
  STELLAR_BILLING_ENABLED = "true"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[checks]
  [checks.health]
    port = 8080
    type = "http"
    interval = "30s"
    timeout = "5s"
    path = "/api/v1/health"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

### 5.2 환경변수 (Fly Secrets)

```bash
# Database
fly secrets set STELLAR_DB_URL="postgresql://..."

# Lemon Squeezy
fly secrets set LEMON_API_KEY="..."
fly secrets set LEMON_STORE_ID="..."
fly secrets set LEMON_VARIANT_PRO="..."
fly secrets set LEMON_VARIANT_TEAM="..."
fly secrets set LEMON_WEBHOOK_SECRET="..."

# Stripe
fly secrets set STRIPE_SECRET_KEY="sk_live_..."
fly secrets set STRIPE_WEBHOOK_SECRET="whsec_..."
fly secrets set STRIPE_PRICE_PRO="price_..."
fly secrets set STRIPE_PRICE_TEAM="price_..."

# TossPayments
fly secrets set TOSS_SECRET_KEY="live_sk_..."
fly secrets set TOSS_CLIENT_KEY="live_ck_..."
fly secrets set TOSS_WEBHOOK_SECRET="..."
```

### 5.3 도메인 설정

```bash
fly certs create api.stellar-memory.com
# DNS: CNAME api.stellar-memory.com → stellar-memory-api.fly.dev
```

### 5.4 배포 체크리스트 (Infrastructure Steps)

아래는 코드 외 인프라 설정 단계로, 실제 배포 시 수행:

1. **Neon PostgreSQL 프로비저닝** (F4-2)
   - Neon 콘솔에서 프로젝트 생성 (Region: AWS ap-northeast-1)
   - pgvector 확장 활성화: `CREATE EXTENSION IF NOT EXISTS vector;`
   - Connection string을 `STELLAR_DB_URL`에 설정
   - 서버 코드: `asyncpg.create_pool(db_url)` 으로 연결 (server.py startup)

2. **Fly Secrets 설정** (F4-3)
   - 위 5.2 섹션의 모든 `fly secrets set` 명령 실행
   - 코드: `BillingConfig` 의 각 `*_env` 필드에서 환경변수명 참조
   - `docker-compose.yml`에도 모든 env var가 주석으로 문서화됨

3. **Domain + SSL** (F4-4)
   - `fly certs create api.stellar-memory.com`
   - DNS에 CNAME 레코드 추가: `api → stellar-memory-api.fly.dev`
   - Landing page CHECKOUT_URLS에서 `https://api.stellar-memory.com` 참조

4. **Health Check 확인** (F4-5)
   - `fly.toml`의 `[checks.health]` 섹션이 `/api/v1/health` 엔드포인트를 30초 간격 모니터링
   - 기존 `server.py`의 `/api/v1/health` 엔드포인트 활용

---

## 6. Landing Page 결제 UI

### 6.1 결제 수단 선택 모달

Pro/Team CTA 클릭 시 표시되는 모달:

```html
<!-- 결제 모달 -->
<div id="checkout-modal" class="modal" style="display:none;">
  <div class="modal-content">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <h3 class="modal-title">Subscribe to <span id="modal-tier">Pro</span></h3>
    <p class="modal-price" id="modal-price">$29/mo</p>

    <div class="checkout-options">
      <!-- Lemon Squeezy (기본) -->
      <button class="checkout-btn checkout-primary" onclick="checkout('lemonsqueezy')">
        <span class="checkout-icon">🍋</span>
        <span class="checkout-label">Pay with Card</span>
        <span class="checkout-sub">Global - Tax included</span>
      </button>

      <!-- Stripe -->
      <button class="checkout-btn" onclick="checkout('stripe')">
        <span class="checkout-icon">💳</span>
        <span class="checkout-label">Pay with Stripe</span>
        <span class="checkout-sub">Global - Card payments</span>
      </button>

      <!-- 토스페이먼츠 -->
      <button class="checkout-btn" onclick="checkout('toss')">
        <span class="checkout-icon">🇰🇷</span>
        <span class="checkout-label">토스페이먼츠로 결제</span>
        <span class="checkout-sub">한국 - 카드/계좌이체</span>
      </button>
    </div>
  </div>
</div>
```

### 6.2 모달 CSS

```css
.modal {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: var(--bg-card);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: 32px;
  max-width: 420px; width: 90%;
  position: relative;
}
.modal-close {
  position: absolute; top: 12px; right: 16px;
  background: none; border: none; color: var(--text-muted);
  font-size: 1.5rem; cursor: pointer;
}
.modal-title {
  font-size: 1.3rem; font-weight: 700; color: var(--text-primary);
  margin-bottom: 4px;
}
.modal-price {
  font-size: 1rem; color: var(--accent-gold); margin-bottom: 24px;
}
.checkout-options { display: flex; flex-direction: column; gap: 12px; }
.checkout-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-primary); cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  text-align: left;
}
.checkout-btn:hover {
  border-color: rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.08);
}
.checkout-primary {
  border-color: var(--accent-gold);
  background: rgba(240,180,41,0.08);
}
.checkout-icon { font-size: 1.5rem; }
.checkout-label { font-size: 0.95rem; font-weight: 600; }
.checkout-sub { font-size: 0.75rem; color: var(--text-muted); margin-left: auto; }
```

### 6.3 결제 JavaScript

```javascript
const CHECKOUT_URLS = {
  lemonsqueezy: {
    pro: "https://stellar-memory.lemonsqueezy.com/checkout/buy/VARIANT_PRO",
    team: "https://stellar-memory.lemonsqueezy.com/checkout/buy/VARIANT_TEAM"
  },
  stripe: {
    pro: "https://api.stellar-memory.com/billing/stripe/checkout?tier=pro",
    team: "https://api.stellar-memory.com/billing/stripe/checkout?tier=team"
  },
  toss: {
    pro: "https://api.stellar-memory.com/billing/toss/checkout?tier=pro",
    team: "https://api.stellar-memory.com/billing/toss/checkout?tier=team"
  }
};

function openCheckoutModal(tier) {
  var prices = { pro: "$29/mo", team: "$99/mo" };
  document.getElementById("modal-tier-name").textContent = tier.charAt(0).toUpperCase() + tier.slice(1);
  document.getElementById("modal-price-text").textContent = prices[tier] || "$29/mo";
  document.getElementById("checkout-modal").style.display = "flex";
  document.getElementById("checkout-modal").dataset.tier = tier;
}

function closeCheckoutModal() {
  document.getElementById("checkout-modal").style.display = "none";
}

function doCheckout(provider) {
  var tier = document.getElementById("checkout-modal").dataset.tier;
  var url = CHECKOUT_URLS[provider] && CHECKOUT_URLS[provider][tier];
  if (url) {
    if (provider === "lemonsqueezy") {
      window.open(url, "_blank");
    } else {
      window.location.href = url;
    }
  }
  closeCheckoutModal();
}

// "Coming Soon" 버튼을 결제 버튼으로 교체
// Pro CTA: onclick="openCheckoutModal('pro')"
// Team CTA: onclick="openCheckoutModal('team')"
```

### 6.4 Pricing 카드 CTA 변경

**Before (Phase 1):**
```html
<a href="#" class="pricing-cta pricing-cta-gold">Coming Soon</a>
```

**After (Phase 2):**
```html
<a href="javascript:void(0)" onclick="openCheckoutModal('pro')"
   class="pricing-cta pricing-cta-gold">Subscribe</a>
```

---

## 7. Webhook 처리 통합

### 7.1 통합 Webhook 핸들러

```python
# stellar_memory/billing/webhooks.py

from stellar_memory.auth import AuthManager

async def handle_subscription_event(event: WebhookEvent, auth_mgr: AuthManager):
    """모든 Provider의 구독 이벤트를 통합 처리"""

    if event.event_type == "subscription_created":
        # 1. 사용자 존재 확인 (없으면 생성)
        user = await get_or_create_user(db, event.customer_email, event.provider)
        # 2. tier 업데이트
        user.tier = event.plan_tier
        user.provider_subscription_id = event.subscription_id
        await db.commit()
        # 3. API Key 자동 발급 (첫 구독 시)
        if not await has_api_key(db, user.id):
            key = generate_api_key()
            await create_api_key(db, user.id, key)
            await send_welcome_email(user.email, key)

    elif event.event_type == "subscription_cancelled":
        user = await get_user_by_email(db, event.customer_email)
        # Grace period: 현 결제 기간 끝까지 유지
        # ends_at 기록, 만료 시 tier → free

    elif event.event_type == "subscription_expired":
        user = await get_user_by_email(db, event.customer_email)
        user.tier = "free"
        await db.commit()

    # 이벤트 로깅
    await log_subscription_event(db, event)
```

### 7.2 FastAPI Webhook 라우터

```python
# server.py에 추가

@app.post("/webhook/lemonsqueezy")
async def lemon_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("X-Signature", "")
    event = await lemon_provider.verify_webhook(payload, sig)
    await handle_subscription_event(event, db)
    return {"ok": True}

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    event = await stripe_provider.verify_webhook(payload, sig)
    await handle_subscription_event(event, db)
    return {"ok": True}

@app.post("/webhook/toss")
async def toss_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Toss-Signature", "")
    event = await toss_provider.verify_webhook(payload, sig)
    await handle_subscription_event(event, db)
    return {"ok": True}
```

---

## 8. Implementation Checklist

### F1: 결제 시스템
- [ ] F1-1: PaymentProvider 추상화 (base.py)
- [ ] F1-2: Lemon Squeezy Provider 구현
- [ ] F1-3: Stripe Provider 구현
- [ ] F1-4: TossPayments Provider 구현
- [ ] F1-5: Webhook 통합 핸들러
- [ ] F1-6: Landing page 결제 모달 + JS
- [ ] F1-7: Pricing CTA "Coming Soon" → "Subscribe" 전환

### F2: 사용자 & API Key
- [ ] F2-1: DB 스키마 (users, api_keys, subscription_events)
- [ ] F2-2: 사용자 등록 API (/auth/register)
- [ ] F2-3: API Key CRUD API (/auth/api-keys)
- [ ] F2-4: 인증 미들웨어 리팩토링 (key_hash 기반)

### F3: Tier 제한
- [ ] F3-1: Tier 설정 모듈 (tiers.py)
- [ ] F3-2: Rate Limit tier별 적용
- [ ] F3-3: Memory count enforcement

### F4: Cloud 배포
- [ ] F4-1: fly.toml 생성
- [ ] F4-2: Neon PostgreSQL 연결
- [ ] F4-3: Fly Secrets 설정
- [ ] F4-4: api.stellar-memory.com 도메인
- [ ] F4-5: Health check + 모니터링

---

## 9. File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `stellar_memory/billing/__init__.py` | CREATE | 빌링 패키지 초기화 |
| `stellar_memory/billing/base.py` | CREATE | PaymentProvider 추상화 |
| `stellar_memory/billing/lemonsqueezy.py` | CREATE | Lemon Squeezy 연동 |
| `stellar_memory/billing/stripe_provider.py` | CREATE | Stripe 연동 |
| `stellar_memory/billing/toss_provider.py` | CREATE | 토스페이먼츠 연동 |
| `stellar_memory/billing/tiers.py` | CREATE | Tier 설정 + enforcement |
| `stellar_memory/billing/webhooks.py` | CREATE | 통합 Webhook 핸들러 |
| `stellar_memory/auth.py` | CREATE | 사용자 등록 + API Key 관리 |
| `stellar_memory/models.py` | CREATE | DB 스키마 (SQLAlchemy) |
| `stellar_memory/server.py` | MODIFY | 새 라우터 추가 |
| `stellar_memory/config.py` | MODIFY | 빌링 설정 추가 |
| `fly.toml` | CREATE | Fly.io 배포 설정 |
| `landing/index.html` | MODIFY | 결제 모달 + JS + CTA 변경 |
| `pyproject.toml` | MODIFY | 의존성 추가 |
| `docker-compose.yml` | MODIFY | 환경변수 추가 |

---

## 10. Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| 기본 결제 Provider | Lemon Squeezy | MoR로 VAT/세금 자동 처리, 솔로 개발자에게 최적 |
| Stripe 추가 이유 | 글로벌 대안 | LS보다 낮은 수수료, 더 많은 커스터마이징 |
| 토스 추가 이유 | 국내 사용자 | 한국 카드/계좌이체 지원, UX 최적화 |
| API Key 저장 | SHA-256 해시 | 보안: 원문 저장 안 함, 발급 시 1회만 노출 |
| 배포 플랫폼 | Fly.io | Docker 기반, 글로벌 엣지, 무료 티어, 간단한 설정 |
| DB | Neon PostgreSQL | 서버리스, pgvector 지원, 기존 스키마 호환 |
| 리전 | nrt (Tokyo) | 한국에서 가장 낮은 레이턴시 |
| 결제 UI | 모달 방식 | 페이지 이동 없이 Provider 선택, 기존 랜딩페이지 유지 |
| 토스 정기결제 | 빌링키 방식 | 결제창 SDK → 빌링키 발급 → 서버에서 자동 청구 |

---

## 11. Security Considerations

| 항목 | 대책 |
|------|------|
| Webhook 검증 | 각 Provider별 signature 검증 필수 |
| API Key 저장 | SHA-256 해시만 저장, 원문 절대 저장 안 함 |
| 빌링키 저장 | AES-256 암호화 후 저장 (토스) |
| HTTPS | Fly.io 자동 TLS, 모든 통신 암호화 |
| CORS | api.stellar-memory.com 도메인만 허용 |
| Rate Limiting | Tier별 제한 + IP별 제한 이중 적용 |
| SQL Injection | SQLAlchemy ORM + parameterized queries |

---

## References

- [Lemon Squeezy API](https://docs.lemonsqueezy.com/api)
- [Lemon Squeezy Webhooks](https://docs.lemonsqueezy.com/guides/developer-guide/webhooks)
- [Lemon Squeezy Subscriptions](https://docs.lemonsqueezy.com/guides/developer-guide/managing-subscriptions)
- [Stripe Checkout](https://docs.stripe.com/api/checkout/sessions)
- [Stripe Subscriptions](https://docs.stripe.com/api/subscriptions)
- [TossPayments API](https://docs.tosspayments.com/en/api-guide)
- [TossPayments 자동결제](https://docs.tosspayments.com/guides/v2/billing)
- [python-tosspayments (PyPI)](https://pypi.org/project/python-tosspayments/)
- [lemonsqueezy-py-api (GitHub)](https://github.com/wdonofrio/lemonsqueezy-py-api)
