with open('app/core/signal_extractor.py', 'r') as f:
    content = f.read()
content = content.replace('PERF_SPIKE = "perf_spike"', 'PERF_SPIKE = "perf_spike"\n    RESEARCH_DIGEST = "research_digest"\n    COMPLIANCE_ALERT = "compliance_alert"')
with open('app/core/signal_extractor.py', 'w') as f:
    f.write(content)
print('Fixed')