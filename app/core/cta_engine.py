from typing import Optional
from app.models.enums import CTA
from app.core.opportunity_engine import OpportunityType

class CTAEngine:
    def __init__(self):
        self.cta_map = {
            OpportunityType.RESEARCH_DIGEST: CTA.OPEN_ENDED,
            OpportunityType.COMPLIANCE_ALERT: CTA.BINARY_YES_STOP,
            OpportunityType.PERF_DIP: CTA.BINARY_YES_STOP,
            OpportunityType.PERF_SPIKE: CTA.OPEN_ENDED,
            OpportunityType.MILESTONE_REACHED: CTA.OPEN_ENDED,
            OpportunityType.DORMANT_WITH_VERA: CTA.BINARY_YES_STOP,
            OpportunityType.CUSTOMER_LAPSED_SOFT: CTA.BINARY_YES_STOP,
            OpportunityType.CUSTOMER_LAPSED_HARD: CTA.BINARY_YES_STOP,
            OpportunityType.APPOINTMENT_TOMORROW: CTA.NONE,
            OpportunityType.REVIEW_THEME_EMERGED: CTA.OPEN_ENDED,
            OpportunityType.CURIOUS_ASK_DUE: CTA.OPEN_ENDED,
            OpportunityType.OFFER_OPPORTUNITY: CTA.BINARY_YES_STOP,
            OpportunityType.SEASONAL_OPPORTUNITY: CTA.OPEN_ENDED,
            OpportunityType.TREND_SIGNAL: CTA.OPEN_ENDED,
            OpportunityType.COMPETITOR_CONTEXT: CTA.OPEN_ENDED,
            OpportunityType.INFORMATIONAL_OPPORTUNITY: CTA.NONE,
            OpportunityType.ACTION_OPPORTUNITY: CTA.BINARY_YES_STOP,
            OpportunityType.RECALL_DUE: CTA.MULTI_CHOICE_SLOT,
            OpportunityType.CHRONIC_REFILL_DUE: CTA.BINARY_CONFIRM_CANCEL,
            OpportunityType.TRIAL_FOLLOWUP: CTA.BINARY_YES_STOP,
            OpportunityType.RENEWAL_DUE: CTA.BINARY_YES_STOP,
            OpportunityType.WINBACK_ELIGIBLE: CTA.BINARY_YES_STOP,
            OpportunityType.ACTIVE_PLANNING_INTENT: CTA.BINARY_CONFIRM_CANCEL,
            OpportunityType.SUPPLY_ALERT: CTA.BINARY_YES_STOP,
            OpportunityType.CATEGORY_SEASONAL: CTA.OPEN_ENDED,
            OpportunityType.GBP_UNVERIFIED: CTA.BINARY_YES_STOP,
            OpportunityType.CDE_OPPORTUNITY: CTA.BINARY_YES_STOP,
        }
    
    def select_cta(self, opportunity_type: OpportunityType, scope: str = 'merchant') -> CTA:
        if scope == 'customer':
            if opportunity_type in [OpportunityType.RECALL_DUE, OpportunityType.APPOINTMENT_TOMORROW, OpportunityType.TRIAL_FOLLOWUP]:
                return CTA.MULTI_CHOICE_SLOT
            if opportunity_type == OpportunityType.CHRONIC_REFILL_DUE:
                return CTA.BINARY_CONFIRM_CANCEL
            return CTA.BINARY_YES_STOP
        
        return self.cta_map.get(opportunity_type, CTA.OPEN_ENDED)
    
    def get_cta_text(self, cta: CTA, language: str = 'en') -> str:
        if language.startswith('hi'):
            cta_texts = {
                CTA.BINARY_YES_STOP: 'YES / STOP',
                CTA.BINARY_CONFIRM_CANCEL: 'CONFIRM / CANCEL',
                CTA.OPEN_ENDED: '',
                CTA.MULTI_CHOICE_SLOT: '1 / 2 / Time',
                CTA.NONE: '',
            }
        else:
            cta_texts = {
                CTA.BINARY_YES_STOP: 'YES / STOP',
                CTA.BINARY_CONFIRM_CANCEL: 'CONFIRM / CANCEL',
                CTA.OPEN_ENDED: '',
                CTA.MULTI_CHOICE_SLOT: '1 / 2 / Time',
                CTA.NONE: '',
            }
        return cta_texts.get(cta, '')
