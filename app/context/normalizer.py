from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.category import CategoryContext
from app.models.merchant import MerchantContext
from app.models.trigger import TriggerContext
from app.models.customer import CustomerContext
from app.models.enums import ContextScope

class NormalizedContext(BaseModel):
    category: Optional[CategoryContext] = None
    merchant: Optional[MerchantContext] = None
    trigger: Optional[TriggerContext] = None
    customer: Optional[CustomerContext] = None
    facts: List[str] = []
    raw_category: Optional[Dict[str, Any]] = None
    raw_merchant: Optional[Dict[str, Any]] = None
    raw_trigger: Optional[Dict[str, Any]] = None
    raw_customer: Optional[Dict[str, Any]] = None

    def ensure_consistency(self) -> bool:
        if self.category is None or self.merchant is None or self.trigger is None:
            raise ValueError("Category, Merchant, and Trigger are required")
        return True


class ContextNormalizer:
    def normalize(
        self,
        category: Dict[str, Any],
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None
    ) -> NormalizedContext:
        normalized = NormalizedContext(
            category=CategoryContext(**category),
            merchant=MerchantContext(**merchant),
            trigger=TriggerContext(**trigger),
            customer=CustomerContext(**customer) if customer else None,
            facts=[],
            raw_category=category,
            raw_merchant=merchant,
            raw_trigger=trigger,
            raw_customer=customer
        )
        return normalized