from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import time

from app.config.settings import settings
from app.models.request_models import (
    ContextPushBody, TickBody, ReplyBody, Action, TickResponse, ReplyResponse, HealthResponse, MetadataResponse
)
from app.context.normalizer import ContextNormalizer
from app.context.fact_ledger import FactLedger  # per-request instances, NOT global singleton
from app.core.signal_extractor import SignalExtractor
from app.core.opportunity_engine import OpportunityEngine, OpportunityType, trigger_kind_to_opportunity_type
from app.core.suppression import SuppressionEngine
from app.core.cta_engine import CTAEngine
from app.retrieval.structured_retriever import StructuredRetriever, GroundedContext
from app.llm.ollama_client import get_llm_provider
from app.llm.composer import Composer, MessageCompose
from app.validation.validator import Validator
from app.conversation.state import StateManager, ConversationRepository, ConversationState, EngagementState
from app.conversation.graph import create_reply_graph, process_reply
from app.core.intent_router import IntentRouter

# Global stores
context_store: Dict[str, Any] = {}
context_versions: Dict[str, int] = {}
raw_contexts: Dict[str, Dict] = {}

# Initialize components
normalizer = ContextNormalizer()
signal_extractor = SignalExtractor()
opportunity_engine = OpportunityEngine()
suppression = SuppressionEngine()
cta_engine = CTAEngine()
retriever = StructuredRetriever()
llm_provider = get_llm_provider()
composer = Composer(llm_provider)
validator = Validator()
conversation_repo = ConversationRepository()
state_manager = StateManager(conversation_repo)
intent_router = IntentRouter()

app = FastAPI(title="Vera AI Merchant Assistant", version="1.0.0")

# Track server start time for uptime_seconds
_START_TIME = time.time()

# Build the LangGraph reply graph (once at startup)
_reply_graph = create_reply_graph(
    state_manager=state_manager,
    intent_router=intent_router,
    suppression=suppression,
    opportunity_engine=opportunity_engine,
    retriever=retriever,
    composer=composer,
    validator=validator,
    context_store=context_store,
)

@app.get("/v1/healthz", response_model=HealthResponse)
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
        uptime_seconds=int(time.time() - _START_TIME),
        contexts_loaded=counts
    )

@app.get("/v1/debug/context")
async def debug_context():
    return {
        "context_store_keys": list(context_store.keys()),
        "raw_contexts_keys": list(raw_contexts.keys()),
        "context_versions": context_versions
    }

@app.get("/v1/metadata", response_model=MetadataResponse)
async def metadata():
    return MetadataResponse(
        team_name="Team Vera",
        team_members=["AI Engineer"],
        model=settings.OLLAMA_MODEL,
        approach="Deterministic opportunity engine + grounded retrieval + LLM composition + validation",
        contact_email="team@vera.ai",
        version="1.0.0",
        submitted_at=datetime.now().isoformat() + "Z"
    )

@app.post("/v1/context")
async def push_context(body: ContextPushBody):
    scope = body.scope
    context_id = body.context_id
    version = body.version
    
    # Use string value of scope for consistent key format
    scope_str = scope.value if hasattr(scope, 'value') else str(scope)
    key = f"{scope_str}:{context_id}"
    current_version = context_versions.get(key, 0)
    
    if version <= current_version:
        return {
            "accepted": False,
            "reason": "stale_version",
            "current_version": current_version
        }
    
    raw_contexts[key] = body.payload
    context_versions[key] = version
    
    if scope.value in ["category", "merchant", "trigger", "customer"]:
        merchant_id = None
        category_slug = None
        trigger_id = None
        customer_id = None
        
        if scope == "merchant":
            merchant_id = body.payload.get("merchant_id")
            category_slug = body.payload.get("category_slug")
        elif scope == "category":
            category_slug = body.payload.get("slug")
        elif scope == "trigger":
            merchant_id = body.payload.get("merchant_id")
            customer_id = body.payload.get("customer_id")
            trigger_id = body.payload.get("id")
            if merchant_id:
                m_raw = raw_contexts.get(f"merchant:{merchant_id}")
                if m_raw:
                    category_slug = m_raw.get("category_slug")
        
        if merchant_id and category_slug:
            merchant_key = f"merchant:{merchant_id}"
            category_key = f"category:{category_slug}"
            
            trigger_key = None
            for k, v in raw_contexts.items():
                if k.startswith("trigger:") and v.get("merchant_id") == merchant_id:
                    trigger_key = k
                    break
            
            if merchant_key in raw_contexts and category_key in raw_contexts and trigger_key:
                normalized = normalizer.normalize(
                    category=raw_contexts[category_key],
                    merchant=raw_contexts[merchant_key],
                    trigger=raw_contexts[trigger_key],
                    customer=raw_contexts.get(f"customer:{customer_id}") if customer_id else None
                )
                
                # Per-request FactLedger — scoped to this merchant/context, no cross-pollution
                per_req_ledger = FactLedger()
                per_req_ledger.extract_from_context(normalized)
                normalized.facts = [f.fact_id for f in per_req_ledger.get_verified_facts()]

                context_store[f"merchant:{merchant_id}"] = normalized
                context_store["normalized"] = normalized
    
    return {
        "accepted": True,
        "ack_id": f"ack_{context_id}_v{version}",
        "stored_at": datetime.now().isoformat() + "Z"
    }

@app.post("/v1/tick", response_model=TickResponse)
async def tick(body: TickBody):
    actions = []
    
    for trigger_id in body.available_triggers:
        trigger_key = f"trigger:{trigger_id}"
        if trigger_key not in raw_contexts:
            continue
        
        trigger = raw_contexts[trigger_key]
        merchant_id = trigger.get("merchant_id")
        customer_id = trigger.get("customer_id")
        
        if not merchant_id:
            continue
        
        opp_type = trigger_kind_to_opportunity_type(trigger.get("kind", ""))
        should_suppress, reason = suppression.should_suppress(merchant_id, trigger_id, opp_type.value, "")
        if should_suppress:
            continue
        
        normalized = context_store.get(f"merchant:{merchant_id}")
        if not normalized:
            merchant_key = f"merchant:{merchant_id}"
            category_slug = raw_contexts.get(merchant_key, {}).get("category_slug")
            if category_slug:
                category_key = f"category:{category_slug}"
                if category_key in raw_contexts:
                    normalized = normalizer.normalize(
                        category=raw_contexts[category_key],
                        merchant=raw_contexts[merchant_key],
                        trigger=trigger,
                        customer=raw_contexts.get(f"customer:{customer_id}") if customer_id else None
                    )
                    # Per-request FactLedger — isolated
                    per_req_ledger = FactLedger()
                    per_req_ledger.extract_from_context(normalized)
                    normalized.facts = [f.fact_id for f in per_req_ledger.get_verified_facts()]
                    context_store[f"merchant:{merchant_id}"] = normalized
        
        if not normalized:
            continue
        
        context_store["normalized"] = normalized
        
        signals = signal_extractor.extract_signals(normalized)
        
        opportunity = opportunity_engine.select_best_opportunity(normalized, signals, suppression, trigger.get("kind"))
        if not opportunity:
            continue
        
        grounded = retriever.retrieve_for_opportunity(normalized, opportunity)
        
        composed = composer.compose(grounded, opportunity.value, trigger.get("kind", ""))
        
        validation = validator.validate(composed, grounded, [], composed.cta)
        if not validation.valid:
            composed = validator.repair(composed, grounded, composed.cta)
            validation.fallback_used = True
        
        cta = cta_engine.select_cta(opportunity, trigger.get("scope", "merchant"))
        
        suppression.record_send(merchant_id, trigger_id, opportunity.value, composed.body, 
                               datetime.fromisoformat(trigger.get("expires_at").replace("Z", "+00:00")) if trigger.get("expires_at") else None)
        
        conversation_id = f"conv_{merchant_id}_{trigger_id}_{int(datetime.now().timestamp())}"
        
        action = Action(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            send_as="merchant_on_behalf" if customer_id else "vera",
            trigger_id=trigger_id,
            template_name=f"vera_{trigger.get('kind', 'generic')}_v1",
            template_params=[normalized.merchant.identity.owner_first_name or normalized.merchant.identity.name, 
                           trigger.get("kind", ""), ""],
            body=composed.body,
            cta=cta.value,
            suppression_key=trigger.get("suppression_key", ""),
            rationale=composed.rationale
        )
        actions.append(action)
        
        state_manager.create_conversation(
            merchant_id=merchant_id,
            customer_id=customer_id,
            opportunity=opportunity.value
        )
    
    return TickResponse(actions=actions)


# Legacy compatibility alias (kept for any external scripts that reference it)
def map_trigger_to_opportunity(trigger_kind: str) -> OpportunityType:
    """Deprecated: use trigger_kind_to_opportunity_type from opportunity_engine instead."""
    return trigger_kind_to_opportunity_type(trigger_kind)

@app.post("/v1/reply", response_model=ReplyResponse)
async def reply(body: ReplyBody):
    """
    Handle merchant reply via LangGraph conversation orchestration.
    Intent routing: interested → action_flow, stop → graceful_exit,
    auto-reply → suppress, not_now → wait, question → answer_question, etc.
    """
    # Ensure conversation state exists
    conv_state = state_manager.get_state(body.conversation_id)
    if not conv_state:
        conv_state = state_manager.create_conversation(
            merchant_id=body.merchant_id or "",
            customer_id=body.customer_id,
            conversation_id=body.conversation_id,
        )

    # Record incoming message
    state_manager.add_message(body.conversation_id, "merchant", body.message, None)

    # Run through LangGraph
    result = process_reply(
        conversation_id=body.conversation_id,
        merchant_id=body.merchant_id or conv_state.merchant_id,
        message=body.message,
        turn_number=body.turn_number,
        graph=_reply_graph,
        context_store=context_store,
        customer_id=body.customer_id,
    )

    return ReplyResponse(
        action=result["action"],
        body=result.get("body"),
        cta=result.get("cta"),
        wait_seconds=result.get("wait_seconds"),
        rationale=result.get("rationale", ""),
    )


@app.post("/v1/teardown")
async def teardown():
    """Reset in-memory state (used by judge between test runs)."""
    context_store.clear()
    context_versions.clear()
    raw_contexts.clear()
    
    # Clear database
    import sqlite3
    try:
        conn = sqlite3.connect("vera.db")
        conn.execute("DELETE FROM conversations")
        conn.commit()
        conn.close()
    except Exception:
        pass
        
    return {"status": "ok", "cleared": True}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)