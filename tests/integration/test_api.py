"""
Integration tests for /v1/context, /v1/tick, and /v1/reply endpoints.
These tests POST to the running server.
"""
import pytest
import json
import time
from urllib import request as req, error as urlerror

BASE = "http://localhost:8080"


def post(path, body, timeout=35):
    data = json.dumps(body).encode()
    r = req.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
    try:
        with req.urlopen(r, timeout=timeout) as resp:
            return json.loads(resp.read()), resp.status
    except urlerror.HTTPError as e:
        return json.loads(e.read()), e.code


def get(path, timeout=10):
    with req.urlopen(f"{BASE}{path}", timeout=timeout) as resp:
        return json.loads(resp.read()), resp.status


def load_fixtures():
    cat = json.load(open("dataset/categories/dentists.json"))
    mseed = json.load(open("dataset/merchants_seed.json"))
    m = mseed["merchants"][0]
    tseed = json.load(open("dataset/triggers_seed.json"))
    triggers = tseed.get("triggers", tseed) if isinstance(tseed, dict) else tseed
    trg = next((x for x in triggers if x.get("merchant_id") == m["merchant_id"]), triggers[0])
    return cat, m, trg


@pytest.fixture(scope="module")
def pushed_context():
    """Push category, merchant, trigger. Returns (merchant_id, trigger_id)."""
    post("/v1/teardown", {})
    
    cat, m, trg = load_fixtures()
    mid = m["merchant_id"]
    tid = trg["id"]
    
    v = int(time.time() * 1000)
    post("/v1/context", {"scope": "category", "context_id": "dentists",
                         "version": v, "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"})
    post("/v1/context", {"scope": "merchant", "context_id": mid,
                         "version": v, "payload": m, "delivered_at": "2026-09-27T10:00:00Z"})
    post("/v1/context", {"scope": "trigger", "context_id": tid,
                         "version": v, "payload": trg, "delivered_at": "2026-09-27T10:00:00Z"})
    return mid, tid


# ---------------------------------------------------------------------------
# /v1/healthz
# ---------------------------------------------------------------------------

class TestHealthz:
    def test_healthz_returns_200(self):
        r, status = get("/v1/healthz")
        assert status == 200

    def test_healthz_schema(self):
        r, _ = get("/v1/healthz")
        assert "status" in r
        assert "uptime_seconds" in r
        assert "contexts_loaded" in r
        assert r["status"] == "ok"

    def test_contexts_loaded_has_all_scopes(self):
        r, _ = get("/v1/healthz")
        cl = r["contexts_loaded"]
        assert "category" in cl
        assert "merchant" in cl
        assert "customer" in cl
        assert "trigger" in cl


# ---------------------------------------------------------------------------
# /v1/context
# ---------------------------------------------------------------------------

class TestContextPush:
    def test_category_push_accepted(self):
        cat = json.load(open("dataset/categories/dentists.json"))
        v = int(time.time() * 1000)
        r, status = post("/v1/context", {
            "scope": "category", "context_id": "dentists_test",
            "version": v, "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"
        })
        assert status == 200
        assert r.get("accepted") is True


    def test_stale_version_rejected(self):
        cat = json.load(open("dataset/categories/dentists.json"))
        v = int(time.time() * 1000)
        # Push current version
        post("/v1/context", {
            "scope": "category", "context_id": "stale_test",
            "version": v, "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"
        })
        # Push older version (stale)
        r, status = post("/v1/context", {
            "scope": "category", "context_id": "stale_test",
            "version": v - 1, "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"
        })
        assert status == 200
        assert r.get("accepted") is False
        assert r.get("reason") == "stale_version"

    def test_invalid_scope_rejected(self):
        r, status = post("/v1/context", {
            "scope": "invalid_scope", "context_id": "test",
            "version": 1, "payload": {}, "delivered_at": "2026-09-27T10:00:00Z"
        })
        assert status == 422  # FastAPI validation error

    def test_context_push_triggers_normalization(self, pushed_context):
        """After pushing category+merchant+trigger, debug endpoint should show normalized context."""
        mid, tid = pushed_context
        r, _ = get("/v1/debug/context")
        norm_keys = r.get("context_store_keys", [])
        assert f"merchant:{mid}" in norm_keys, (
            f"Normalization at push time failed (Bug 3). Got keys: {norm_keys}"
        )


# ---------------------------------------------------------------------------
# /v1/tick
# ---------------------------------------------------------------------------

class TestTick:
    def test_tick_empty_triggers_returns_empty_actions(self):
        r, status = post("/v1/tick", {"now": "2026-09-27T10:00:00Z", "available_triggers": []})
        assert status == 200
        assert r.get("actions") == []

    def test_tick_with_valid_context_returns_action(self, pushed_context):
        mid, tid = pushed_context
        r, status = post("/v1/tick", {"now": "2026-09-27T10:00:00Z", "available_triggers": [tid]},
                         timeout=35)
        assert status == 200, f"Tick returned {status}: {r}"
        actions = r.get("actions", [])
        assert len(actions) >= 1, "Expected at least one action from valid context"

    def test_tick_action_has_required_fields(self, pushed_context):
        mid, tid = pushed_context
        r, status = post("/v1/tick", {"now": "2026-09-27T10:00:00Z", "available_triggers": [tid]},
                         timeout=35)
        assert status == 200
        if r.get("actions"):
            a = r["actions"][0]
            assert "conversation_id" in a
            assert "merchant_id" in a
            assert "body" in a
            assert a["body"]  # non-empty
            assert "cta" in a
            assert "suppression_key" in a
            assert "rationale" in a

    def test_tick_action_body_non_empty(self, pushed_context):
        mid, tid = pushed_context
        r, status = post("/v1/tick", {"now": "2026-09-27T10:00:00Z", "available_triggers": [tid]},
                         timeout=35)
        assert status == 200
        if r.get("actions"):
            assert r["actions"][0]["body"].strip() != ""


# ---------------------------------------------------------------------------
# /v1/reply
# ---------------------------------------------------------------------------

class TestReply:
    def test_reply_yes_returns_send(self):
        r, status = post("/v1/reply", {
            "conversation_id": "test_yes_001",
            "merchant_id": "m_001",
            "customer_id": None,
            "from_role": "merchant",
            "message": "Yes, send me the details",
            "received_at": "2026-09-27T10:45:00Z",
            "turn_number": 2
        })
        assert status == 200
        assert r.get("action") in ("send", "wait")

    def test_reply_auto_pattern_returns_end(self):
        r, status = post("/v1/reply", {
            "conversation_id": "test_auto_001",
            "merchant_id": "m_001",
            "customer_id": None,
            "from_role": "merchant",
            "message": "Thank you for contacting us. Our team will respond shortly.",
            "received_at": "2026-09-27T10:46:00Z",
            "turn_number": 2
        })
        assert status == 200
        assert r.get("action") == "send", f"Auto-reply should return send for 1st nudge, got: {r}"

    def test_reply_stop_returns_end(self):
        r, status = post("/v1/reply", {
            "conversation_id": "test_stop_001",
            "merchant_id": "m_001",
            "customer_id": None,
            "from_role": "merchant",
            "message": "Stop",
            "received_at": "2026-09-27T10:47:00Z",
            "turn_number": 2
        })
        assert status == 200
        assert r.get("action") == "end"

    def test_reply_not_interested_returns_end(self):
        r, status = post("/v1/reply", {
            "conversation_id": "test_ni_001",
            "merchant_id": "m_001",
            "customer_id": None,
            "from_role": "merchant",
            "message": "not interested",
            "received_at": "2026-09-27T10:48:00Z",
            "turn_number": 2
        })
        assert status == 200
        assert r.get("action") == "end"

    def test_reply_not_now_returns_wait(self):
        r, status = post("/v1/reply", {
            "conversation_id": "test_notnow_001",
            "merchant_id": "m_001",
            "customer_id": None,
            "from_role": "merchant",
            "message": "not now, maybe later",
            "received_at": "2026-09-27T10:49:00Z",
            "turn_number": 2
        })
        assert status == 200
        assert r.get("action") == "wait"

    def test_reply_response_has_rationale(self):
        r, status = post("/v1/reply", {
            "conversation_id": "test_rationale_001",
            "merchant_id": "m_001",
            "customer_id": None,
            "from_role": "merchant",
            "message": "ok",
            "received_at": "2026-09-27T10:50:00Z",
            "turn_number": 2
        })
        assert status == 200
        assert r.get("rationale"), "Reply must include a rationale"
