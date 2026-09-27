with open('app/core/opportunity_engine.py', 'r') as f:
    content = f.read()

# Update select_best_opportunity to accept trigger_kind and prefer matching opportunities
old_sig = '''    def select_best_opportunity(self, normalized, signals: List[Signal], suppression) -> Optional[OpportunityType]:'''

new_sig = '''    def select_best_opportunity(self, normalized, signals: List[Signal], suppression, trigger_kind: str = None) -> Optional[OpportunityType]:'''

content = content.replace(old_sig, new_sig)

# Update the method body to use trigger_kind
old_body = '''        # If no opportunities from signals, create from trigger kind directly
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
                    opportunities.append(opp)'''

new_body = '''        # If no opportunities from signals, create from trigger kind directly
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
            trigger_kind_to_opp = {
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
                "supply_alert": OpportunityType.SUPPLY_ALERT,
            }
            preferred_type = trigger_kind_to_opp.get(trigger_kind)
            if preferred_type:
                for opp in opportunities:
                    if opp.type == preferred_type:
                        opp.score += 10  # Boost score for trigger-matched opportunity
                        break'''

content = content.replace(old_body, new_body)

# Update the tick endpoint call to pass trigger_kind
old_call = '''        opportunity = opportunity_engine.select_best_opportunity(normalized, signals, suppression)'''
new_call = '''        opportunity = opportunity_engine.select_best_opportunity(normalized, signals, suppression, trigger.get("kind"))'''

content = content.replace(old_call, new_call)

with open('app/core/opportunity_engine.py', 'w') as f:
    f.write(content)
print('Fixed')