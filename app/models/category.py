from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.models.enums import ContextScope, TriggerScope, TriggerSource, SendAs, CTA

class OfferTemplate(BaseModel):
    id: str
    title: str
    value: str
    audience: str
    type: str

class VoiceProfile(BaseModel):
    tone: str
    register: str
    code_mix: str
    vocab_allowed: List[str]
    vocab_taboo: List[str]
    salutation_examples: List[str]
    tone_examples: List[str]

class PeerStats(BaseModel):
    scope: str
    avg_rating: float
    avg_review_count: int
    avg_views_30d: float
    avg_calls_30d: float
    avg_directions_30d: float
    avg_ctr: float
    avg_photos: int
    avg_post_freq_days: int
    retention_6mo_pct: Optional[float] = None
    monthly_churn_pct: Optional[float] = None
    trial_to_paid_pct: Optional[float] = None
    delivery_share_pct: Optional[float] = None
    repeat_customer_pct: Optional[float] = None

class DigestItem(BaseModel):
    id: str
    kind: str
    title: str
    source: str
    summary: Optional[str] = None
    trial_n: Optional[int] = None
    patient_segment: Optional[str] = None
    actionable: Optional[str] = None
    date: Optional[str] = None
    credits: Optional[int] = None
    fee: Optional[str] = None

class ContentItem(BaseModel):
    id: str
    title: str
    channel: str
    length_seconds: int
    body: str

class SeasonalBeat(BaseModel):
    month_range: str
    note: str

class TrendSignal(BaseModel):
    query: str
    delta_yoy: float
    segment_age: str
    skew: str

class CategoryContext(BaseModel):
    slug: str
    display_name: str
    voice: VoiceProfile
    offer_catalog: List[OfferTemplate]
    peer_stats: PeerStats
    digest: List[DigestItem]
    patient_content_library: List[ContentItem]
    seasonal_beats: List[SeasonalBeat]
    trend_signals: List[TrendSignal]
    regulatory_authorities: Optional[List[str]] = None
    professional_journals: Optional[List[str]] = None