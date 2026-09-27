from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class SignalType(str, Enum):
    PERF_SPIKE = "perf_spike"
    PERF_DIP = "perf_dip"
    PERF_SPIKE_UP = "perf_spike"
    MILESTONE_REACHED = "milestone_reached"
    DORMANT_WITH_VERA = "dormant_with_vera"
    CUSTOMER_LAPSED_SOFT = "customer_lapsed_soft"
    CUSTOMER_LAPSED_HARD = "customer_lapsed_hard"
    OFFER_OPPORTUNITY = "offer_opportunity"
    SEASONAL_OPPORTUNITY = "seasonal_opportunity"
    TREND_SIGNAL = "trend_signal"
    REVIEW_THEME_EMERGED = "review_theme_emerged"
    COMPETITOR_OPENED = "competitor_opened"
    CURIOUS_ASK_DUE = "curious_ask_due"
    ACTIVE_PLANNING_INTENT = "active_planning_intent"
    SUPPLY_ALERT = "supply_alert"
    CATEGORY_SEASONAL = "category_seasonal"
    INFORMATIONAL_OPPORTUNITY = "informational_opportunity"
    ACTION_OPPORTUNITY = "action_opportunity"
    RECALL_DUE = "recall_due"
    CHRONIC_REFILL_DUE = "chronic_refill_due"
    RESEARCH_DIGEST = "research_digest"
    COMPLIANCE_ALERT = "compliance_alert"
    APPOINTMENT_TOMORROW = "appointment_tomorrow"
    TRIAL_FOLLOWUP = "trial_followup"
    RENEWAL_DUE = "renewal_due"
    WINBACK_ELIGIBLE = "winback_eligible"
    GBP_UNVERIFIED = "gbp_unverified"
    CDE_OPPORTUNITY = "cde_opportunity"

class Signal(BaseModel):
    type: SignalType
    priority: int
    urgency: int
    source: str
    facts: List[str] = []
    recommended_action: str
    expires_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "priority": self.priority,
            "urgency": self.urgency,
            "source": self.source,
            "facts": self.facts,
            "recommended_action": self.recommended_action,
            "expires_at": self.expires_at
        }

class SignalExtractor:
    def __init__(self):
        pass
    
    def extract_signals(self, normalized) -> List[Signal]:
        signals = []
        
        if normalized.merchant:
            m = normalized.merchant
            
            if m.signals:
                for s in m.signals:
                    if "stale_posts" in s:
                        signals.append(Signal(
                            type=SignalType.INFORMATIONAL_OPPORTUNITY,
                            priority=3,
                            urgency=2,
                            source="merchant.signals",
                            facts=["merchant.stale_posts"],
                            recommended_action="post_reminder",
                            expires_at=None
                        ))
                    if "ctr_below_peer_median" in s:
                        signals.append(Signal(
                            type=SignalType.PERF_DIP,
                            priority=4,
                            urgency=4,
                            source="merchant.signals",
                            facts=["merchant.ctr_below_peer_median"],
                            recommended_action="ctr_improvement",
                            expires_at=None
                        ))
                    if "perf_dip_severe" in s:
                        signals.append(Signal(
                            type=SignalType.PERF_DIP,
                            priority=5,
                            urgency=5,
                            source="merchant.signals",
                            facts=["merchant.perf_dip_severe"],
                            recommended_action="ctr_improvement",
                            expires_at=None
                        ))
                    if "high_risk_adult_cohort" in s:
                        signals.append(Signal(
                            type=SignalType.INFORMATIONAL_OPPORTUNITY,
                            priority=3,
                            urgency=3,
                            source="merchant.signals",
                            facts=["merchant.high_risk_adult_cohort"],
                            recommended_action="patient_recall",
                            expires_at=None
                        ))
                    if "renewal_due_soon" in s:
                        signals.append(Signal(
                            type=SignalType.RENEWAL_DUE,
                            priority=4,
                            urgency=4,
                            source="merchant.signals",
                            facts=["merchant.renewal_due_soon"],
                            recommended_action="renewal_reminder",
                            expires_at=None
                        ))
                    if "winback_eligible" in s:
                        signals.append(Signal(
                            type=SignalType.WINBACK_ELIGIBLE,
                            priority=3,
                            urgency=3,
                            source="merchant.signals",
                            facts=["merchant.winback_eligible"],
                            recommended_action="winback_campaign",
                            expires_at=None
                        ))
                    if "dormant_with_vera" in s:
                        signals.append(Signal(
                            type=SignalType.DORMANT_WITH_VERA,
                            priority=2,
                            urgency=2,
                            source="merchant.signals",
                            facts=["merchant.dormant_with_vera"],
                            recommended_action="re_engage",
                            expires_at=None
                        ))
                    if "unverified_gbp" in s:
                        signals.append(Signal(
                            type=SignalType.GBP_UNVERIFIED,
                            priority=3,
                            urgency=3,
                            source="merchant.signals",
                            facts=["merchant.unverified_gbp"],
                            recommended_action="verify_gbp",
                            expires_at=None
                        ))
                    if "no_active_offers" in s:
                        signals.append(Signal(
                            type=SignalType.OFFER_OPPORTUNITY,
                            priority=3,
                            urgency=2,
                            source="merchant.signals",
                            facts=["merchant.no_active_offers"],
                            recommended_action="create_offer",
                            expires_at=None
                        ))
            
            if m.performance:
                perf = m.performance
                if perf.delta_7d.get("views_pct", 0) < -0.2:
                    signals.append(Signal(
                        type=SignalType.PERF_DIP,
                        priority=4,
                        urgency=4,
                        source="merchant.performance",
                        facts=["merchant.performance.views_dip"],
                        recommended_action="investigate_dip",
                        expires_at=None
                    ))
                if perf.delta_7d.get("views_pct", 0) > 0.2:
                    signals.append(Signal(
                        type=SignalType.PERF_SPIKE,
                        priority=3,
                        urgency=2,
                        source="merchant.performance",
                        facts=["merchant.performance.views_spike"],
                        recommended_action="capitalize_spike",
                        expires_at=None
                    ))
                if perf.ctr and perf.ctr < 0.02:
                    signals.append(Signal(
                        type=SignalType.PERF_DIP,
                        priority=4,
                        urgency=3,
                        source="merchant.performance",
                        facts=["merchant.performance.low_ctr"],
                        recommended_action="improve_ctr",
                        expires_at=None
                    ))
        
        if normalized.trigger:
            t = normalized.trigger
            if t.kind == "research_digest":
                signals.append(Signal(
                    type=SignalType.RESEARCH_DIGEST,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.research_digest",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="share_research",
                    expires_at=t.expires_at
                ))
            elif t.kind == "perf_dip":
                signals.append(Signal(
                    type=SignalType.PERF_DIP,
                    priority=5,
                    urgency=t.urgency,
                    source="trigger.perf_dip",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="address_perf_dip",
                    expires_at=t.expires_at
                ))
            elif t.kind == "recall_due":
                signals.append(Signal(
                    type=SignalType.RECALL_DUE,
                    priority=4,
                    urgency=t.urgency,
                    source="trigger.recall_due",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="send_recall",
                    expires_at=t.expires_at
                ))
            elif t.kind == "competitor_opened":
                signals.append(Signal(
                    type=SignalType.COMPETITOR_OPENED,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.competitor_opened",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="competitor_response",
                    expires_at=t.expires_at
                ))
            elif t.kind == "milestone_reached":
                signals.append(Signal(
                    type=SignalType.MILESTONE_REACHED,
                    priority=2,
                    urgency=t.urgency,
                    source="trigger.milestone_reached",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="celebrate_milestone",
                    expires_at=t.expires_at
                ))
            elif t.kind == "review_theme_emerged":
                signals.append(Signal(
                    type=SignalType.REVIEW_THEME_EMERGED,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.review_theme_emerged",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="address_reviews",
                    expires_at=t.expires_at
                ))
            elif t.kind == "curious_ask_due":
                signals.append(Signal(
                    type=SignalType.CURIOUS_ASK_DUE,
                    priority=2,
                    urgency=t.urgency,
                    source="trigger.curious_ask_due",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="ask_question",
                    expires_at=t.expires_at
                ))
            elif t.kind == "active_planning_intent":
                signals.append(Signal(
                    type=SignalType.ACTIVE_PLANNING_INTENT,
                    priority=5,
                    urgency=t.urgency,
                    source="trigger.active_planning_intent",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="execute_plan",
                    expires_at=t.expires_at
                ))
            elif t.kind == "supply_alert":
                signals.append(Signal(
                    type=SignalType.SUPPLY_ALERT,
                    priority=5,
                    urgency=t.urgency,
                    source="trigger.supply_alert",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="alert_customers",
                    expires_at=t.expires_at
                ))
            elif t.kind == "renewal_due":
                signals.append(Signal(
                    type=SignalType.RENEWAL_DUE,
                    priority=4,
                    urgency=t.urgency,
                    source="trigger.renewal_due",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="renewal_reminder",
                    expires_at=t.expires_at
                ))
            elif t.kind == "seasonal_perf_dip":
                signals.append(Signal(
                    type=SignalType.SEASONAL_OPPORTUNITY,
                    priority=2,
                    urgency=t.urgency,
                    source="trigger.seasonal_perf_dip",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="seasonal_reframe",
                    expires_at=t.expires_at
                ))
            elif t.kind == "winback_eligible":
                signals.append(Signal(
                    type=SignalType.WINBACK_ELIGIBLE,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.winback_eligible",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="winback_campaign",
                    expires_at=t.expires_at
                ))
            elif t.kind == "chronic_refill_due":
                signals.append(Signal(
                    type=SignalType.CHRONIC_REFILL_DUE,
                    priority=4,
                    urgency=t.urgency,
                    source="trigger.chronic_refill_due",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="refill_reminder",
                    expires_at=t.expires_at
                ))
            elif t.kind == "trial_followup":
                signals.append(Signal(
                    type=SignalType.TRIAL_FOLLOWUP,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.trial_followup",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="followup_trial",
                    expires_at=t.expires_at
                ))
            elif t.kind == "category_seasonal":
                signals.append(Signal(
                    type=SignalType.CATEGORY_SEASONAL,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.category_seasonal",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="seasonal_prep",
                    expires_at=t.expires_at
                ))
            elif t.kind == "gbp_unverified":
                signals.append(Signal(
                    type=SignalType.GBP_UNVERIFIED,
                    priority=3,
                    urgency=t.urgency,
                    source="trigger.gbp_unverified",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="verify_gbp",
                    expires_at=t.expires_at
                ))
            elif t.kind == "cde_opportunity":
                signals.append(Signal(
                    type=SignalType.CDE_OPPORTUNITY,
                    priority=2,
                    urgency=t.urgency,
                    source="trigger.cde_opportunity",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="cde_invite",
                    expires_at=t.expires_at
                ))
            elif t.kind == "festival_upcoming":
                signals.append(Signal(
                    type=SignalType.SEASONAL_OPPORTUNITY,
                    priority=2,
                    urgency=t.urgency,
                    source="trigger.festival_upcoming",
                    facts=[f"trigger.{t.kind}"],
                    recommended_action="festival_campaign",
                    expires_at=t.expires_at
                ))
        
        return signals