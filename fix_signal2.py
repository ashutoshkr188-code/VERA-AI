with open('app/core/signal_extractor.py', 'r') as f:
    content = f.read()
# Add missing signal types
new_types = '''
    RESEARCH_DIGEST = "research_digest"
    COMPLIANCE_ALERT = "compliance_alert"
    APPOINTMENT_TOMORROW = "appointment_tomorrow"
    TRIAL_FOLLOWUP = "trial_followup"
    RENEWAL_DUE = "renewal_due"
    WINBACK_ELIGIBLE = "winback_eligible"
    ACTIVE_PLANNING_INTENT = "active_planning_intent"
    CDE_OPPORTUNITY = "cde_opportunity"
    GBP_UNVERIFIED = "gbp_unverified"
'''
content = content.replace('PERF_SPIKE = "perf_spike"', 'PERF_SPIKE = "perf_spike"' + new_types)
with open('app/core/signal_extractor.py', 'w') as f:
    f.write(content)
print('Fixed')