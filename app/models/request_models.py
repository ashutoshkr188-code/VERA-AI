from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.models.enums import ContextScope, TriggerScope, TriggerSource, SendAs, CTA

class ContextPushBody(BaseModel):
    scope: ContextScope
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str

class TickBody(BaseModel):
    now: str
    available_triggers: List[str] = []

class Action(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    send_as: SendAs
    trigger_id: str
    template_name: str
    template_params: List[str]
    body: str
    cta: str
    suppression_key: str
    rationale: str

class TickResponse(BaseModel):
    actions: List[Action] = []

class ReplyBody(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: str
    turn_number: int

class ReplyResponse(BaseModel):
    action: str
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: int
    contexts_loaded: Dict[str, int]

class MetadataResponse(BaseModel):
    team_name: str
    team_members: List[str]
    model: str
    approach: str
    contact_email: str
    version: str
    submitted_at: str