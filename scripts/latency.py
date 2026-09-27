import time
import json
import statistics
from urllib import request as req

BASE = "http://localhost:8080"

def post(path, body):
    data = json.dumps(body).encode()
    r = req.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with req.urlopen(r, timeout=35) as resp:
        result = json.loads(resp.read())
    return result, time.time() - t0

def main():
    print("Preparing context...")
    # Push category, merchant, trigger
    cat = json.load(open("dataset/categories/dentists.json"))
    post("/v1/context", {"scope": "category", "context_id": "dentists", "version": 20, "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"})
    
    mseed = json.load(open("dataset/merchants_seed.json"))
    m = mseed["merchants"][0]
    mid = m["merchant_id"]
    post("/v1/context", {"scope": "merchant", "context_id": mid, "version": 20, "payload": m, "delivered_at": "2026-09-27T10:00:00Z"})
    
    tseed = json.load(open("dataset/triggers_seed.json"))
    tseed = tseed.get("triggers", tseed) if isinstance(tseed, dict) else tseed
    trg = next((x for x in tseed if x.get("merchant_id") == mid), tseed[0])
    tid = trg["id"]
    post("/v1/context", {"scope": "trigger", "context_id": tid, "version": 20, "payload": trg, "delivered_at": "2026-09-27T10:00:00Z"})

    print("Running 10 tick requests...")
    tick_times = []
    for _ in range(10):
        try:
            _, t = post("/v1/tick", {"now": "2026-09-27T10:30:00Z", "available_triggers": [tid]})
            tick_times.append(t)
        except Exception as e:
            print(f"Tick failed: {e}")

    print("Running 10 reply requests...")
    reply_times = []
    for i in range(10):
        try:
            _, t = post("/v1/reply", {
                "conversation_id": f"lat_test_{i}",
                "merchant_id": mid,
                "customer_id": None,
                "from_role": "merchant",
                "message": "Yes please",
                "received_at": "2026-09-27T10:45:00Z",
                "turn_number": 2
            })
            reply_times.append(t)
        except Exception as e:
            print(f"Reply failed: {e}")

    def report(name, times):
        if not times: return
        print(f"--- {name} ---")
        print(f"Min: {min(times):.2f}s")
        print(f"Max: {max(times):.2f}s")
        print(f"Mean: {statistics.mean(times):.2f}s")
        print(f"Median: {statistics.median(times):.2f}s")
        print(f"P95: {sorted(times)[int(len(times)*0.95)]:.2f}s")

    report("Tick Latency", tick_times)
    report("Reply Latency", reply_times)

if __name__ == "__main__":
    main()
