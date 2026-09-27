from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from app.core.signal_extractor import Signal, SignalType

class OpportunityType(str, Enum):
    RESEARCH_DIGEST = "research_digest"
    COMPLIANCE_ALERT = "compliance_alert"
    PERF_DIP = "perf_dip"
    PERF_SPIKE = "perf_spike"
    MILESTONE_REACHED = "milestone_reached"
    DORMANT_WITH_VERA = "dormant_with_vera"
    CUSTOMER_LAPSED_SOFT = "customer_lapsed_soft"
    CUSTOMER_LAPSED_HARD = "customer_lapsed_hard"
    APPOINTMENT_TOMORROW = "appointment_tomorrow"
    REVIEW_THEME_EMERGED = "review_theme_emerged"
    CURIOUS_ASK_DUE = "curious_ask_due"
    OFFER_OPPORTUNITY = "offer_opportunity"
    SEASONAL_OPPORTUNITY = "seasonal_opportunity"
    TREND_SIGNAL = "trend_signal"
    COMPETITOR_CONTEXT = "competitor_context"
    INFORMATIONAL_OPPORTUNITY = "informational_opportunity"
    ACTION_OPPORTUNITY = "action_opportunity"
    RECALL_DUE = "recall_due"
    CHRONIC_REFILL_DUE = "chronic_refill_due"
    TRIAL_FOLLOWUP = "trial_followup"
    RENEWAL_DUE = "renewal_due"
    WINBACK_ELIGIBLE = "winback_eligible"
    ACTIVE_PLANNING_INTENT = "active_planning_intent"
    SUPPLY_ALERT = "supply_alert"
    CATEGORY_SEASONAL = "category_seasonal"
    GBP_UNVERIFIED = "gbp_unverified"
    CDE_OPPORTUNITY = "cde_opportunity"

# ---------------------------------------------------------------------------
# Authoritative trigger-kind → OpportunityType mapping.
# This is the single source of truth. All callers import this constant.
# ---------------------------------------------------------------------------
TRIGGER_KIND_TO_OPPORTUNITY: Dict[str, "OpportunityType"] = {}
# (populated after OpportunityType is defined below)


class Opportunity(BaseModel):
    type: OpportunityType
    trigger_id: str
    signals: List[str] = []
    score: float = 0.0
    urgency: int = 1
    merchant_relevance: int = 1
    trigger_relevance: int = 1
    category_fit: int = 1
    merchant_fit: int = 1
    customer_relevance: int = 0
    specificity: int = 1
    freshness: int = 1
    engagement_potential: int = 1
    repetition_penalty: int = 0
    missing_fact_penalty: int = 0
    confidence: float = 1.0
    expires_at: Optional[str] = None

    def calculate_score(self) -> float:
        weights = {
            "urgency_weight": 3,
            "merchant_relevance_weight": 2,
            "trigger_relevance_weight": 2,
            "specificity_weight": 3,
            "freshness_weight": 2,
            "engagement_weight": 2,
            "repetition_penalty_weight": -5,
            "missing_fact_penalty_weight": -3
        }
        
        score = 0
        score += self.urgency * weights["urgency_weight"]
        score += self.merchant_relevance * weights["merchant_relevance_weight"]
        score += self.trigger_relevance * weights["trigger_relevance_weight"]
        score += self.specificity * weights["specificity_weight"]
        score += self.freshness * weights["freshness_weight"]
        score += self.engagement_potential * weights["engagement_weight"]
        score += self.repetition_penalty * weights["repetition_penalty_weight"]
        score += self.missing_fact_penalty * weights["missing_fact_penalty_weight"]
        
        self.score = score
        return score

# ---------------------------------------------------------------------------
# Populate the mapping now that OpportunityType is defined.
# ---------------------------------------------------------------------------
TRIGGER_KIND_TO_OPPORTUNITY = {
    "research_digest": OpportunityType.RESEARCH_DIGEST,
    "regulation_change": OpportunityType.COMPLIANCE_ALERT,
    "perf_dip": OpportunityType.PERF_DIP,
    "perf_spike": OpportunityType.PERF_SPIKE,
    "milestone_reached": OpportunityType.MILESTONE_REACHED,
    "dormant_with_vera": OpportunityType.DORMANT_WITH_VERA,
    "customer_lapsed_soft": OpportunityType.CUSTOMER_LAPSED_SOFT,
    "customer_lapsed_hard": OpportunityType.CUSTOMER_LAPSED_HARD,
    "appointment_tomorrow": OpportunityType.APPOINTMENT_TOMORROW,
    "review_theme_emerged": OpportunityType.REVIEW_THEME_EMERGED,
    "curious_ask_due": OpportunityType.CURIOUS_ASK_DUE,
    "festival_upcoming": OpportunityType.SEASONAL_OPPORTUNITY,
    "competitor_opened": OpportunityType.COMPETITOR_CONTEXT,
    "category_trend_movement": OpportunityType.TREND_SIGNAL,
    "recall_due": OpportunityType.RECALL_DUE,
    "chronic_refill_due": OpportunityType.CHRONIC_REFILL_DUE,
    "trial_followup": OpportunityType.TRIAL_FOLLOWUP,
    "renewal_due": OpportunityType.RENEWAL_DUE,
    "winback_eligible": OpportunityType.WINBACK_ELIGIBLE,
    "active_planning_intent": OpportunityType.ACTIVE_PLANNING_INTENT,
    "supply_alert": OpportunityType.SUPPLY_ALERT,
    "category_seasonal": OpportunityType.CATEGORY_SEASONAL,
    "gbp_unverified": OpportunityType.GBP_UNVERIFIED,
    "cde_opportunity": OpportunityType.CDE_OPPORTUNITY,
    "seasonal_perf_dip": OpportunityType.SEASONAL_OPPORTUNITY,
    "ipl_match_today": OpportunityType.SEASONAL_OPPORTUNITY,
    "wedding_package_followup": OpportunityType.ACTION_OPPORTUNITY,
}



def trigger_kind_to_opportunity_type(trigger_kind: str) -> "OpportunityType":
    """Look up OpportunityType for a trigger kind. Falls back to INFORMATIONAL_OPPORTUNITY."""
    return TRIGGER_KIND_TO_OPPORTUNITY.get(trigger_kind, OpportunityType.INFORMATIONAL_OPPORTUNITY)


class OpportunityEngine:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.weights = self.config.get("weights", {
            "urgency_weight": 3,
            "merchant_relevance_weight": 2,
            "trigger_relevance_weight": 2,
            "specificity_weight": 3,
            "freshness_weight": 2,
            "engagement_weight": 2,
            "repetition_penalty_weight": -5,
            "missing_fact_penalty_weight": -3
        })
    
    def select_best_opportunity(self, normalized, signals: List[Signal], suppression, trigger_kind: str = None) -> Optional[OpportunityType]:
        opportunities = []
        
        # First, try to create opportunities from signals
        for signal in signals:
            opp = self._signal_to_opportunity(signal, normalized)
            if opp:
                should_suppress, _ = suppression.should_suppress(
                    normalized.merchant.merchant_id,
                    normalized.trigger.id,
                    opp.type.value,
                    ""
                )
                if not should_suppress:
                    opp.calculate_score()
                    opportunities.append(opp)
        
        # If no opportunities from signals, create from trigger kind directly
        if not opportunities and normalized.trigger:
            opp = self._trigger_to_opportunity(normalized.trigger, normalized)
            if opp:
                should_suppress, _ = suppression.should_suppress(
                    normalized.merchant.merchant_id,
                    normalized.trigger.id,
                    opp.type.value,
                    ""
                )
                if not should_suppress:
                    opp.calculate_score()
                    opportunities.append(opp)
        
        # If trigger_kind provided, boost score of matching opportunity
        if trigger_kind and opportunities:
            preferred_type = TRIGGER_KIND_TO_OPPORTUNITY.get(trigger_kind)
            if preferred_type:
                for opp in opportunities:
                    if opp.type == preferred_type:
                        opp.score += 10  # Boost score for trigger-matched opportunity
                        break
        
        if not opportunities:
            return None
        
        # Sort by score descending
        opportunities.sort(key=lambda x: x.score, reverse=True)
        return opportunities[0].type
    
    def _trigger_to_opportunity(self, trigger, normalized) -> Optional[Opportunity]:
        """Create opportunity directly from trigger kind using canonical mapping."""
        opp_type = TRIGGER_KIND_TO_OPPORTUNITY.get(trigger.kind)
        if not opp_type:
            return None

        merchant_relevance = 2
        trigger_relevance = 3
        specificity = 2
        freshness = 2
        engagement = 2

        if normalized.merchant and normalized.merchant.signals:
            if "high_risk_adult_cohort" in normalized.merchant.signals:
                merchant_relevance = 3

        if trigger.kind in ["research_digest", "regulation_change", "supply_alert"]:
            trigger_relevance = 3
            specificity = 3

        return Opportunity(
            type=opp_type,
            trigger_id=trigger.id,
            signals=[trigger.kind],
            urgency=trigger.urgency,
            merchant_relevance=merchant_relevance,
            trigger_relevance=trigger_relevance,
            category_fit=2,
            merchant_fit=2,
            specificity=specificity,
            freshness=freshness,
            engagement_potential=engagement,
        )
    
    def _signal_to_opportunity(self, signal: Signal, normalized) -> Optional[Opportunity]:
        signal_type_to_opp = {
            SignalType.RESEARCH_DIGEST: OpportunityType.RESEARCH_DIGEST,
            SignalType.COMPLIANCE_ALERT: OpportunityType.COMPLIANCE_ALERT,
            SignalType.PERF_DIP: OpportunityType.PERF_DIP,
            SignalType.PERF_SPIKE: OpportunityType.PERF_SPIKE,
            SignalType.MILESTONE_REACHED: OpportunityType.MILESTONE_REACHED,
            SignalType.DORMANT_WITH_VERA: OpportunityType.DORMANT_WITH_VERA,
            SignalType.CUSTOMER_LAPSED_SOFT: OpportunityType.CUSTOMER_LAPSED_SOFT,
            SignalType.CUSTOMER_LAPSED_HARD: OpportunityType.CUSTOMER_LAPSED_HARD,
            SignalType.APPOINTMENT_TOMORROW: OpportunityType.APPOINTMENT_TOMORROW,
            SignalType.REVIEW_THEME_EMERGED: OpportunityType.REVIEW_THEME_EMERGED,
            SignalType.CURIOUS_ASK_DUE: OpportunityType.CURIOUS_ASK_DUE,
            SignalType.OFFER_OPPORTUNITY: OpportunityType.OFFER_OPPORTUNITY,
            SignalType.SEASONAL_OPPORTUNITY: OpportunityType.SEASONAL_OPPORTUNITY,
            SignalType.TREND_SIGNAL: OpportunityType.TREND_SIGNAL,
            SignalType.COMPETITOR_OPENED: OpportunityType.COMPETITOR_CONTEXT,
            SignalType.INFORMATIONAL_OPPORTUNITY: OpportunityType.INFORMATIONAL_OPPORTUNITY,
            SignalType.ACTION_OPPORTUNITY: OpportunityType.ACTION_OPPORTUNITY,
            SignalType.RECALL_DUE: OpportunityType.RECALL_DUE,
            SignalType.CHRONIC_REFILL_DUE: OpportunityType.CHRONIC_REFILL_DUE,
            SignalType.TRIAL_FOLLOWUP: OpportunityType.TRIAL_FOLLOWUP,
            SignalType.RENEWAL_DUE: OpportunityType.RENEWAL_DUE,
            SignalType.WINBACK_ELIGIBLE: OpportunityType.WINBACK_ELIGIBLE,
            SignalType.ACTIVE_PLANNING_INTENT: OpportunityType.ACTIVE_PLANNING_INTENT,
            SignalType.SUPPLY_ALERT: OpportunityType.SUPPLY_ALERT,
            SignalType.CATEGORY_SEASONAL: OpportunityType.CATEGORY_SEASONAL,
            SignalType.GBP_UNVERIFIED: OpportunityType.GBP_UNVERIFIED,
            SignalType.CDE_OPPORTUNITY: OpportunityType.CDE_OPPORTUNITY,
        }
        
        opp_type = signal_type_to_opp.get(signal.type)
        if not opp_type:
            return None
        
        # Calculate relevance scores
        merchant_relevance = 2
        trigger_relevance = 3
        category_fit = 2
        merchant_fit = 2
        specificity = 2
        freshness = 2
        engagement = 2
        
        if normalized.merchant and normalized.merchant.signals:
            if "high_risk_adult_cohort" in normalized.merchant.signals:
                merchant_relevance = 3
        
        if signal.type in [SignalType.RESEARCH_DIGEST, SignalType.COMPLIANCE_ALERT]:
            trigger_relevance = 3
            specificity = 3
        
        return Opportunity(
            type=opp_type,
            trigger_id=normalized.trigger.id,
            signals=[signal.type.value],
            urgency=signal.urgency,
            merchant_relevance=merchant_relevance,
            trigger_relevance=trigger_relevance,
            category_fit=category_fit,
            merchant_fit=merchant_fit,
            specificity=specificity,
            freshness=freshness,
            engagement_potential=engagement,
        )