with open('app/main.py', 'r') as f:
    content = f.read()

# Add a debug endpoint to check context_store
old_health = '''@app.get("/v1/healthz", response_model=HealthResponse)
async def healthz():
    counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
    for key in raw_contexts:
        if key.startswith("category:"):
            counts["category"] += 1
        elif key.startswith("merchant:"):
            counts["merchant"] += 1
        elif key.startswith("customer:"):
            counts["customer"] += 1
        elif key.startswith("trigger:"):
            counts["trigger"] += 1
    
    return HealthResponse(
        status="ok",
        uptime_seconds=0,
        contexts_loaded=counts
    )'''

new_health = '''@app.get("/v1/healthz", response_model=HealthResponse)
async def healthz():
    counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
    for key in raw_contexts:
        if key.startswith("category:"):
            counts["category"] += 1
        elif key.startswith("merchant:"):
            counts["merchant"] += 1
        elif key.startswith("customer:"):
            counts["customer"] += 1
        elif key.startswith("trigger:"):
            counts["trigger"] += 1
    
    return HealthResponse(
        status="ok",
        uptime_seconds=0,
        contexts_loaded=counts
    )

@app.get("/v1/debug/context")
async def debug_context():
    return {
        "context_store_keys": list(context_store.keys()),
        "raw_contexts_keys": list(raw_contexts.keys()),
        "context_versions": context_versions
    }'''

content = content.replace(old_health, new_health)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')