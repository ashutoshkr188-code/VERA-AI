"""
Replay tests for /v1/reply using LangGraph orchestration.
"""
import pytest
import json
from urllib import request as req

BASE = "http://localhost:8080"


def post(path, body, timeout=35):
    data = json.dumps(body).encode()
    r = req.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
    with req.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read()), resp.status


def post_reply(conv_id, mid, msg, turn):
    return post("/v1/reply", {
        "conversation_id": conv_id,
        "merchant_id": mid,
        "message": msg,
        "turn_number": turn,
        "from_role": "merchant",
        "received_at": "2026-09-27T10:05:00Z"
    })

def teardown_server():
    try:
        post("/v1/teardown", {})
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_state():
    teardown_server()
    # Push basic context
    mseed = json.load(open("dataset/merchants_seed.json"))
    m = mseed["merchants"][0]
    mid = m["merchant_id"]
    cat = json.load(open("dataset/categories/dentists.json"))
    
    post("/v1/context", {"scope": "category", "context_id": "dentists", "version": 1, "payload": cat, "delivered_at": "2026-09-27T10:00:00Z"})
    post("/v1/context", {"scope": "merchant", "context_id": mid, "version": 1, "payload": m, "delivered_at": "2026-09-27T10:00:00Z"})
    yield mid


class TestReplyReplay:
    def test_interested_merchant(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_1", mid, "interested", 2)
        assert r["action"] == "send"
        assert r["body"]
    
    def test_yes_send_me_details(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_2", mid, "Yes, send me the details", 2)
        assert r["action"] == "send"
    
    def test_i_want_to_join(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_3", mid, "I want to join", 2)
        assert r["action"] == "send"

    def test_not_interested(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_4", mid, "Not interested", 2)
        assert r["action"] == "end"
        
    def test_maybe_later(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_5", mid, "Maybe later", 2)
        assert r["action"] == "wait"
        assert r["wait_seconds"] > 0

    def test_stop(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_6", mid, "STOP", 2)
        assert r["action"] == "end"

    def test_repeated_auto_reply(self, clean_state):
        mid = clean_state
        msg = "Thank you for your message. We are currently unavailable."
        # 1st time
        r1, _ = post_reply("test_conv_7", mid, msg, 1)
        assert r1["action"] == "send"
        
        # 2nd time
        r2, _ = post_reply("test_conv_7", mid, msg, 2)
        assert r2["action"] == "end"

    def test_question(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_8", mid, "What is this?", 2)
        assert r["action"] == "send"
        assert r["body"]

    def test_curveball(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_9", mid, "How do I file GST?", 2)
        assert r["action"] == "send"
        assert "main topic" in r["body"].lower()

    def test_language_switch_hindi(self, clean_state):
        mid = clean_state
        r, _ = post_reply("test_conv_10", mid, "Mujhe ye chahiye", 2)
        assert r["action"] in ("send", "wait", "end")
