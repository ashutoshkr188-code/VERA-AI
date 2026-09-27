with open('app/main.py', 'r') as f:
    content = f.read()

old_mapping = '''def map_trigger_to_opportunity(trigger_kind: str) -> OpportunityType:
    mapping = {
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
    }
    return mapping.get(trigger_kind, OpportunityType.INFORMATIONAL_OPPORTUNITY)'''

new_mapping = '''def map_trigger_to_opportunity(trigger_kind: str) -> OpportunityType:
    mapping = {
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
        "customer_lapsed_hard": OpportunityType.CUSTOMER_LAPSED_HARD,
        "supply_alert": OpportunityType.SUPPLY_ALERT,
    }
    return mapping.get(trigger_kind, OpportunityType.INFORMATIONAL_OPPORTUNITY)'''

content = content.replace(old_mapping, new_mapping)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')