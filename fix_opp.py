with open('app/core/opportunity_engine.py', 'r') as f:
    content = f.read()

# Update the select_best_opportunity method to handle trigger kinds directly
old_method = '''    def select_best_opportunity(self, normalized, signals: List[Signal], suppression) -> Optional[OpportunityType]:
        if not signals:
            return None
        
        opportunities = []
        
        for signal in signals:
            opp = self._signal_to_opportunity(signal, normalized)
            if opp:
                # Check suppression
                should_suppress, _ = suppression.should_suppress(
                    normalized.merchant.merchant_id,
                    normalized.trigger.id,
                    opp.type.value,
                    ""
                )
                if not should_suppress:
                    opp.calculate_score()
                    opportunities.append(opp)
        
        if not opportunities:
            return None
        
        # Sort by score descending
        opportunities.sort(key=lambda x: x.score, reverse=True)
        return opportunities[0].type'''

new_method = '''    def select_best_opportunity(self, normalized, signals: List[Signal], suppression) -> Optional[OpportunityType]:
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
        
        if not opportunities:
            return None
        
        # Sort by score descending
        opportunities.sort(key=lambda x: x.score, reverse=True)
        return opportunities[0].type
    
    def _trigger_to_opportunity(self, trigger, normalized) -> Optional[Opportunity]:
        """Create opportunity directly from trigger kind."""
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
        
        opp_type = trigger_kind_to_opp.get(trigger.kind)
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
            category_fit=category_fit,
            merchant_fit=merchant_fit,
            specificity=specificity,
            freshness=freshness,
            engagement_potential=engagement,
        )'''

content = content.replace(old_method, new_method)

with open('app/core/opportunity_engine.py', 'w') as f:
    f.write(content)
print('Fixed')