from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.models.enums import ContextScope, TriggerScope, TriggerSource, SendAs, CTA

class TriggerContext(BaseModel):
    id: str
    scope: TriggerScope
    kind: str
    source: TriggerSource
    merchant_id: str
    customer_id: Optional[str] = None
    payload: Dict[str, Any]
    urgency: int
    suppression_key: str
    expires_at: str