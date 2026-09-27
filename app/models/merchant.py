from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.models.enums import ContextScope, TriggerScope, TriggerSource, SendAs, CTA

class Identity(BaseModel):
    name: str
    city: str
    locality: str
    place_id: str
    verified: bool
    languages: List[str]
    owner_first_name: str
    established_year: Optional[int] = None

class Subscription(BaseModel):
    status: str
    plan: str
    days_remaining: Optional[int] = None
    days_since_expiry: Optional[int] = None
    renewed_at: Optional[str] = None

class PerformanceSnapshot(BaseModel):
    window_days: int
    views: int
    calls: int
    directions: int
    ctr: float
    leads: int
    delta_7d: Dict[str, float]

class MerchantOffer(BaseModel):
    id: str
    title: str
    status: str
    started: Optional[str] = None
    ended: Optional[str] = None

class ConversationTurn(BaseModel):
    ts: str
    from_: str = Field(alias="from")
    body: str
    engagement: str

class CustomerAggregate(BaseModel):
    total_unique_ytd: Optional[int] = None
    lapsed_180d_plus: Optional[int] = None
    retention_6mo_pct: Optional[float] = None
    high_risk_adult_count: Optional[int] = None
    lapsed_90d_plus: Optional[int] = None
    retention_3mo_pct: Optional[float] = None
    total_active_members: Optional[int] = None
    monthly_churn_pct: Optional[float] = None
    trial_to_paid_pct: Optional[float] = None
    delivery_orders_30d: Optional[int] = None
    dine_in_orders_30d: Optional[int] = None
    repeat_customer_pct: Optional[float] = None
    delivery_share_pct: Optional[float] = None
    chronic_rx_count: Optional[int] = None

class ReviewTheme(BaseModel):
    theme: str
    sentiment: str
    occurrences_30d: int
    common_quote: Optional[str] = None

class MerchantContext(BaseModel):
    merchant_id: str
    category_slug: str
    identity: Identity
    subscription: Subscription
    performance: PerformanceSnapshot
    offers: List[MerchantOffer]
    conversation_history: List[ConversationTurn]
    customer_aggregate: CustomerAggregate
    signals: List[str]
    review_themes: List[ReviewTheme]