#!/usr/bin/env python3
"""Phase 1A baseline measurement script."""
import time
import json
from urllib import request as req

BASE = "http://localhost:8080"


def post(path, body):
    data = json.dumps(body).encode()
    r = req.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with req.urlopen(r, timeout=35) as resp:
        result = json.loads(resp.read())
    return result, time.time() - t0


def get(path):
    t0 = time.time()
    with req.urlopen(f"{BASE}{path}", timeout=10) as resp:
        result = json.loads(resp.read())
    return result, time.time() - t0


def main():
    print("=== BASELINE MEASUREMENTS ===\n")

    r, t = get("/v1/healthz")
    print(f"GET /v1/healthz:    {t*1000:.0f}ms  -> {r}")

    r, t = get("/v1/metadata")
    print(f"GET /v1/metadata:   {t*1000:.0f}ms  -> model={r.get('model')}")

    # Push category context
    cat = json.load(open("dataset/categories/dentists.json"))
    r, t = post("/v1/context", {
        "scope": "category", "context_id": "dentists", "version": 1,
        "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"
    })
    print(f"POST /v1/context (category): {t*1000:.0f}ms -> accepted={r.get('accepted')}")

    # Push merchant context
    mseed = json.load(open("dataset/merchants_seed.json"))
    m = mseed["merchants"][0]
    mid = m["merchant_id"]
    r, t = post("/v1/context", {
        "scope": "merchant", "context_id": mid, "version": 1,
        "payload": m, "delivered_at": "2026-09-27T10:00:00Z"
    })
    print(f"POST /v1/context (merchant={mid}): {t*1000:.0f}ms -> accepted={r.get('accepted')}")

    # Push trigger context
    tseed_raw = json.load(open("dataset/triggers_seed.json"))
    tseed = tseed_raw.get("triggers", tseed_raw) if isinstance(tseed_raw, dict) else tseed_raw
    trg = next((x for x in tseed if x.get("merchant_id") == mid), tseed[0])
    tid = trg["id"]
    r, t = post("/v1/context", {
        "scope": "trigger", "context_id": tid, "version": 1,
        "payload": trg, "delivered_at": "2026-09-27T10:00:00Z"
    })
    print(f"POST /v1/context (trigger={tid}): {t*1000:.0f}ms -> accepted={r.get('accepted')}")

    # Check context store state
    r, t = get("/v1/debug/context")
    raw_keys = r.get("raw_contexts_keys", [])
    norm_keys = r.get("context_store_keys", [])
    print(f"\nContext store debug:")
    print(f"  raw_contexts keys: {raw_keys}")
    print(f"  context_store keys (normalized): {norm_keys}")
    if not norm_keys:
        print("  [BUG 3 CONFIRMED] Normalization at push time NOT occurring (enum comparison bug)")

    # Tick - calls Ollama
    print(f"\nPOST /v1/tick (triggers=[{tid}]) - calling Ollama, may be slow...")
    try:
        r, t = post("/v1/tick", {"now": "2026-09-27T10:30:00Z", "available_triggers": [tid]})
        actions = r.get("actions", [])
        print(f"  Latency: {t:.2f}s")
        print(f"  Actions returned: {len(actions)}")
        if actions:
            a = actions[0]
            print(f"  body (first 150 chars): {a.get('body','')[:150]}")
            print(f"  cta: {a.get('cta')}")
            print(f"  rationale: {a.get('rationale','')[:100]}")
        else:
            print("  [WARNING] No actions returned from tick")
    except Exception as e:
        print(f"  [ERROR] Tick failed: {e}")

    # Reply tests
    print("\nPOST /v1/reply (yes message)...")
    r, t = post("/v1/reply", {
        "conversation_id": "baseline_test_001",
        "merchant_id": mid,
        "customer_id": None,
        "from_role": "merchant",
        "message": "Yes, send me the details",
        "received_at": "2026-09-27T10:45:00Z",
        "turn_number": 2
    })
    print(f"  Latency: {t*1000:.0f}ms")
    print(f"  action: {r.get('action')}")
    print(f"  body: {r.get('body','')[:100]}")

    print("\nPOST /v1/reply (auto-reply pattern)...")
    r, t = post("/v1/reply", {
        "conversation_id": "baseline_test_002",
        "merchant_id": mid,
        "customer_id": None,
        "from_role": "merchant",
        "message": "Thank you for contacting us. Our team will respond shortly.",
        "received_at": "2026-09-27T10:46:00Z",
        "turn_number": 2
    })
    print(f"  Latency: {t*1000:.0f}ms")
    print(f"  action: {r.get('action')}  (expected: end)")

    print("\nPOST /v1/reply (stop)...")
    r, t = post("/v1/reply", {
        "conversation_id": "baseline_test_003",
        "merchant_id": mid,
        "customer_id": None,
        "from_role": "merchant",
        "message": "Stop",
        "received_at": "2026-09-27T10:47:00Z",
        "turn_number": 2
    })
    print(f"  Latency: {t*1000:.0f}ms")
    print(f"  action: {r.get('action')}  (expected: end)")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
