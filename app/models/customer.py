from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.models.enums import ContextScope, TriggerScope, TriggerSource, SendAs, CTA

class CustomerIdentity(BaseModel):
    name: str
    phone_redacted: Optional[str]
    language_pref: str
    age_band: str

class Relationship(BaseModel):
    first_visit: str
    last_visit: str
    visits_total: int
    services_received: List[str]
    lifetime_value: Optional[int] = None

class Preferences(BaseModel):
    preferred_slots: str
    channel: str
    reminder_opt_in: bool
    preferred_stylist: Optional[str] = None
    wedding_date: Optional[str] = None
    office_nearby: Optional[bool] = None
    family_size: Optional[int] = None
    training_focus: Optional[str] = None
    health_focus: Optional[str] = None
    delivery_address: Optional[str] = None

class Consent(BaseModel):
    opted_in_at: Optional[str]
    scope: List[str]

class CustomerContext(BaseModel):
    customer_id: str
    merchant_id: str
    identity: CustomerIdentity
    relationship: Relationship
    state: str
    preferences: Preferences
    consent: Consent