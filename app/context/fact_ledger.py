from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class FactStatus(str, Enum):
    VERIFIED = "verified"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"

class Fact(BaseModel):
    fact_id: str
    text: str
    value: Optional[float]
    source: str
    field: str
    verified: bool = False
    status: FactStatus = FactStatus.UNAVAILABLE
    confidence: float = 1.0

class FactLedger:
    def __init__(self):
        self._facts: Dict[str, Fact] = {}
        self._fact_id = 0
    
    def add_fact(self,
                 text: str,
                 value: Optional[float],
                 source: str,
                 field: str,
                 verified: bool = False,
                 confidence: float = 1.0,
                 status: FactStatus = FactStatus.UNAVAILABLE) -> str:
        fact_id = f"fact_{self._fact_id}"
        fact = Fact(
            fact_id=fact_id,
            text=text,
            value=value,
            source=source,
            field=field,
            verified=verified,
            status=status,
            confidence=confidence
        )
        self._facts[fact_id] = fact
        self._fact_id += 1
        return fact_id
    
    def get_fact(self, fact_id: str) -> Optional[Fact]:
        return self._facts.get(fact_id)
    
    def get_verified_facts(self) -> List[Fact]:
        return [f for f in self._facts.values() if f.verified]
    
    def get_facts_by_source(self, source: str) -> List[Fact]:
        return [f for f in self._facts.values() if f.source == source]
    
    def extract_from_context(self, normalized) -> Dict[str, Fact]:
        if normalized.merchant:
            m = normalized.merchant
            perf = m.performance
            if perf.views is not None:
                self.add_fact(
                    text=f"Google views: {perf.views}",
                    value=perf.views,
                    source="merchant.performance",
                    field="views",
                    verified=True,
                    status=FactStatus.VERIFIED
                )
            if perf.calls is not None:
                self.add_fact(
                    text=f"Calls: {perf.calls}",
                    value=perf.calls,
                    source="merchant.performance",
                    field="calls",
                    verified=True,
                    status=FactStatus.VERIFIED
                )
            if perf.ctr is not None:
                self.add_fact(
                    text=f"CTR: {perf.ctr:.2%}",
                    value=perf.ctr,
                    source="merchant.performance",
                    field="ctr",
                    verified=True,
                    status=FactStatus.VERIFIED
                )
            if perf.delta_7d.get("views_pct") is not None:
                self.add_fact(
                    text=f"Views change {perf.delta_7d.get('views_pct')}% 7-day",
                    value=perf.delta_7d.get('views_pct'),
                    source="merchant.performance",
                    field="views_change",
                    verified=True,
                    status=FactStatus.VERIFIED
                )
        if normalized.merchant and normalized.merchant.customer_aggregate:
            ca = normalized.merchant.customer_aggregate
            if ca.total_unique_ytd is not None:
                self.add_fact(
                    text=f"Total year-to-date unique customers: {ca.total_unique_ytd}",
                    value=ca.total_unique_ytd,
                    source="merchant.customer_aggregate",
                    field="total_unique_ytd",
                    verified=True,
                    status=FactStatus.VERIFIED
                )
            if ca.lapsed_180d_plus is not None:
                self.add_fact(
                    text=f"Lapsed customers 180d+: {ca.lapsed_180d_plus}",
                    value=ca.lapsed_180d_plus,
                    source="merchant.customer_aggregate",
                    field="lapsed_180d_plus",
                    verified=True,
                    status=FactStatus.VERIFIED
                )
        if normalized.trigger:
            t = normalized.trigger
            if t.payload and isinstance(t.payload, dict):
                for k, v in t.payload.items():
                    if isinstance(v, (int, float)):
                        self.add_fact(
                            text=f"Trigger {k}: {v}",
                            value=v,
                            source="trigger.payload",
                            field=k,
                            verified=True,
                            status=FactStatus.VERIFIED
                        )
        return self._facts

fact_ledger = FactLedger()