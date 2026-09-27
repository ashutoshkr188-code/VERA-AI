from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.category import CategoryContext
from app.models.merchant import MerchantContext
from app.models.trigger import TriggerContext
from app.models.customer import CustomerContext
from app.core.opportunity_engine import Opportunity, OpportunityType
from app.context.fact_ledger import Fact, FactStatus, fact_ledger

class GroundedContext(BaseModel):
    opportunity: Opportunity
    facts: List[Fact]
    merchant: MerchantContext
    category: CategoryContext
    trigger: TriggerContext
    customer: Optional[CustomerContext]
    rationale: str

class StructuredRetriever:
    def __init__(self):
        pass
    
    def retrieve_for_opportunity(self, normalized, opportunity: OpportunityType) -> GroundedContext:
        facts = []
        
        m = normalized.merchant
        c = normalized.category
        t = normalized.trigger
        cust = normalized.customer
        
        # Always include core merchant facts
        if m.performance.views is not None:
            facts.append(Fact(fact_id="merchant_views", text=f"Google views: {m.performance.views}", value=m.performance.views, source="merchant.performance", field="views", verified=True, status=FactStatus.VERIFIED))
        if m.performance.calls is not None:
            facts.append(Fact(fact_id="merchant_calls", text=f"Calls: {m.performance.calls}", value=m.performance.calls, source="merchant.performance", field="calls", verified=True, status=FactStatus.VERIFIED))
        if m.performance.ctr is not None:
            facts.append(Fact(fact_id="merchant_ctr", text=f"CTR: {m.performance.ctr:.2%}", value=m.performance.ctr, source="merchant.performance", field="ctr", verified=True, status=FactStatus.VERIFIED))
        if m.performance.directions is not None:
            facts.append(Fact(fact_id="merchant_directions", text=f"Directions: {m.performance.directions}", value=m.performance.directions, source="merchant.performance", field="directions", verified=True, status=FactStatus.VERIFIED))
        
        # Add delta facts
        if m.performance.delta_7d:
            for k, v in m.performance.delta_7d.items():
                if v is not None:
                    facts.append(Fact(fact_id=f"merchant_delta_{k}", text=f"{k}: {v:+.1%} 7-day", value=v, source="merchant.performance", field=k, verified=True, status=FactStatus.VERIFIED))
        
        # Add customer aggregate facts
        if m.customer_aggregate:
            ca = m.customer_aggregate
            if ca.total_unique_ytd is not None:
                facts.append(Fact(fact_id="ca_total_ytd", text=f"Total YTD customers: {ca.total_unique_ytd}", value=ca.total_unique_ytd, source="merchant.customer_aggregate", field="total_unique_ytd", verified=True, status=FactStatus.VERIFIED))
            if ca.lapsed_180d_plus is not None:
                facts.append(Fact(fact_id="ca_lapsed_180", text=f"Lapsed 180d+: {ca.lapsed_180d_plus}", value=ca.lapsed_180d_plus, source="merchant.customer_aggregate", field="lapsed_180d_plus", verified=True, status=FactStatus.VERIFIED))
            if ca.retention_6mo_pct is not None:
                facts.append(Fact(fact_id="ca_retention_6mo", text=f"6-month retention: {ca.retention_6mo_pct:.0%}", value=ca.retention_6mo_pct, source="merchant.customer_aggregate", field="retention_6mo_pct", verified=True, status=FactStatus.VERIFIED))
            if ca.high_risk_adult_count is not None:
                facts.append(Fact(fact_id="ca_high_risk", text=f"High-risk adult patients: {ca.high_risk_adult_count}", value=ca.high_risk_adult_count, source="merchant.customer_aggregate", field="high_risk_adult_count", verified=True, status=FactStatus.VERIFIED))
            if ca.lapsed_90d_plus is not None:
                facts.append(Fact(fact_id="ca_lapsed_90", text=f"Lapsed 90d+: {ca.lapsed_90d_plus}", value=ca.lapsed_90d_plus, source="merchant.customer_aggregate", field="lapsed_90d_plus", verified=True, status=FactStatus.VERIFIED))
            if ca.retention_3mo_pct is not None:
                facts.append(Fact(fact_id="ca_retention_3mo", text=f"3-month retention: {ca.retention_3mo_pct:.0%}", value=ca.retention_3mo_pct, source="merchant.customer_aggregate", field="retention_3mo_pct", verified=True, status=FactStatus.VERIFIED))
            if ca.total_active_members is not None:
                facts.append(Fact(fact_id="ca_active_members", text=f"Active members: {ca.total_active_members}", value=ca.total_active_members, source="merchant.customer_aggregate", field="total_active_members", verified=True, status=FactStatus.VERIFIED))
            if ca.monthly_churn_pct is not None:
                facts.append(Fact(fact_id="ca_churn", text=f"Monthly churn: {ca.monthly_churn_pct:.1%}", value=ca.monthly_churn_pct, source="merchant.customer_aggregate", field="monthly_churn_pct", verified=True, status=FactStatus.VERIFIED))
            if ca.delivery_orders_30d is not None:
                facts.append(Fact(fact_id="ca_delivery_30d", text=f"Delivery orders 30d: {ca.delivery_orders_30d}", value=ca.delivery_orders_30d, source="merchant.customer_aggregate", field="delivery_orders_30d", verified=True, status=FactStatus.VERIFIED))
            if ca.dine_in_orders_30d is not None:
                facts.append(Fact(fact_id="ca_dinein_30d", text=f"Dine-in orders 30d: {ca.dine_in_orders_30d}", value=ca.dine_in_orders_30d, source="merchant.customer_aggregate", field="dine_in_orders_30d", verified=True, status=FactStatus.VERIFIED))
            if ca.chronic_rx_count is not None:
                facts.append(Fact(fact_id="ca_chronic_rx", text=f"Chronic Rx count: {ca.chronic_rx_count}", value=ca.chronic_rx_count, source="merchant.customer_aggregate", field="chronic_rx_count", verified=True, status=FactStatus.VERIFIED))
        
        # Add peer stats
        if c.peer_stats:
            ps = c.peer_stats
            if ps.avg_ctr is not None:
                facts.append(Fact(fact_id="peer_avg_ctr", text=f"Peer avg CTR: {ps.avg_ctr:.2%}", value=ps.avg_ctr, source="category.peer_stats", field="avg_ctr", verified=True, status=FactStatus.VERIFIED))
            if ps.avg_rating is not None:
                facts.append(Fact(fact_id="peer_avg_rating", text=f"Peer avg rating: {ps.avg_rating}", value=ps.avg_rating, source="category.peer_stats", field="avg_rating", verified=True, status=FactStatus.VERIFIED))
        
        # Add trigger payload facts
        if t.payload and isinstance(t.payload, dict):
            for k, v in t.payload.items():
                if isinstance(v, (int, float, str)):
                    facts.append(Fact(fact_id=f"trigger_{k}", text=f"Trigger {k}: {v}", value=v if isinstance(v, (int, float)) else None, source="trigger.payload", field=k, verified=True, status=FactStatus.VERIFIED))
        
        # Add category digest facts if relevant
        if opportunity == OpportunityType.RESEARCH_DIGEST and c.digest:
            for item in c.digest:
                if item.id == t.payload.get("top_item_id"):
                    facts.append(Fact(fact_id=f"digest_{item.id}", text=f"Digest: {item.title}", value=None, source="category.digest", field=item.id, verified=True, status=FactStatus.VERIFIED))
                    if item.trial_n:
                        facts.append(Fact(fact_id=f"digest_trial_n", text=f"Trial size: {item.trial_n}", value=item.trial_n, source="category.digest", field="trial_n", verified=True, status=FactStatus.VERIFIED))
                    break
        
        # Add active offers
        for offer in m.offers:
            if offer.status == "active":
                facts.append(Fact(fact_id=f"offer_{offer.id}", text=f"Active offer: {offer.title}", value=None, source="merchant.offers", field=offer.id, verified=True, status=FactStatus.VERIFIED))
        
        # Add customer facts if present
        if cust:
            facts.append(Fact(fact_id="cust_name", text=f"Customer: {cust.identity.name}", value=None, source="customer.identity", field="name", verified=True, status=FactStatus.VERIFIED))
            facts.append(Fact(fact_id="cust_state", text=f"State: {cust.state}", value=None, source="customer.relationship", field="state", verified=True, status=FactStatus.VERIFIED))
            if cust.relationship.visits_total is not None:
                facts.append(Fact(fact_id="cust_visits", text=f"Total visits: {cust.relationship.visits_total}", value=cust.relationship.visits_total, source="customer.relationship", field="visits_total", verified=True, status=FactStatus.VERIFIED))
            if cust.preferences.preferred_slots:
                facts.append(Fact(fact_id="cust_pref_slots", text=f"Preferred slots: {cust.preferences.preferred_slots}", value=None, source="customer.preferences", field="preferred_slots", verified=True, status=FactStatus.VERIFIED))
        
        # Build rationale
        rationale_parts = []
        rationale_parts.append(f"Selected opportunity: {opportunity.value}")
        rationale_parts.append(f"Trigger: {t.kind} (urgency: {t.urgency})")
        rationale_parts.append(f"Merchant: {m.identity.name}")
        if m.identity.owner_first_name:
            rationale_parts.append(f"Owner: {m.identity.owner_first_name}")
        rationale_parts.append(f"Retrieved {len(facts)} grounded facts")
        
        opp_obj = Opportunity(type=opportunity, trigger_id=t.id, urgency=t.urgency)
        
        return GroundedContext(
            opportunity=opp_obj,
            facts=facts,
            merchant=m,
            category=c,
            trigger=t,
            customer=cust,
            rationale=". ".join(rationale_parts)
        )