"""
LangGraph-based reply conversation orchestration.
State transitions: intent routing → action handling → composition → validation → response.
"""
from typing import Dict, Any, Optional, List, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END

from app.conversation.state import EngagementState, StateManager
from app.core.intent_router import IntentRouter, Intent
from app.core.suppression import SuppressionEngine
from app.core.opportunity_engine import OpportunityEngine, OpportunityType
from app.retrieval.structured_retriever import StructuredRetriever
from app.llm.composer import Composer, MessageCompose
from app.validation.validator import Validator, ValidationResult
from app.context.fact_ledger import FactLedger
from app.models.enums import CTA


# ---------------------------------------------------------------------------
# State schema for LangGraph (TypedDict required in LangGraph >=0.2)
# ---------------------------------------------------------------------------

class ReplyGraphState(TypedDict, total=False):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    incoming_message: str
    intent: Optional[str]          # Intent.value string
    route: str
    grounded_context: Any          # GroundedContext or None
    composed_message: Any          # MessageCompose or None
    validation_result: Any         # ValidationResult or None
    final_action: str              # "send" | "wait" | "end"
    final_body: str
    final_cta: str
    rationale: str
    wait_seconds: int


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def create_reply_graph(
    state_manager: StateManager,
    intent_router: IntentRouter,
    suppression: SuppressionEngine,
    opportunity_engine: OpportunityEngine,
    retriever: StructuredRetriever,
    composer: Composer,
    validator: Validator,
    context_store: Dict,
):
    """Build and compile the reply conversation graph."""

    # -----------------------------------------------------------------------
    # Node: load_state
    # -----------------------------------------------------------------------
    def load_state(state: ReplyGraphState) -> ReplyGraphState:
        conv_state = state_manager.get_state(state["conversation_id"])
        updates: ReplyGraphState = {}
        if conv_state:
            if not state.get("merchant_id"):
                updates["merchant_id"] = conv_state.merchant_id
            if conv_state.customer_id:
                updates["customer_id"] = conv_state.customer_id
        return updates

    # -----------------------------------------------------------------------
    # Node: analyze_intent
    # -----------------------------------------------------------------------
    def analyze_intent(state: ReplyGraphState) -> ReplyGraphState:
        message = state.get("incoming_message", "")
        conv_state = state_manager.get_state(state.get("conversation_id", ""))
        history = []
        if conv_state:
            history = [m.get("body", "") for m in conv_state.message_history]

        intent = intent_router.detect(message, history)
        route = intent_router.route(intent)
        return {"intent": intent.value, "route": route}

    # -----------------------------------------------------------------------
    # Node: handle_interested  (action_flow)
    # -----------------------------------------------------------------------
    def handle_interested(state: ReplyGraphState) -> ReplyGraphState:
        mid = state.get("merchant_id", "")
        conv_state = state_manager.get_state(state.get("conversation_id", ""))
        current_opp_str = conv_state.current_opportunity if conv_state else None

        try:
            opp_type = OpportunityType(current_opp_str) if current_opp_str else OpportunityType.INFORMATIONAL_OPPORTUNITY
        except ValueError:
            opp_type = OpportunityType.INFORMATIONAL_OPPORTUNITY

        norm_ctx = context_store.get(f"merchant:{mid}") or context_store.get("normalized")
        if norm_ctx:
            grounded = retriever.retrieve_for_opportunity(norm_ctx, opp_type)
            msg = composer.compose(grounded, opp_type.value, opp_type.value)
            return {
                "grounded_context": grounded,
                "composed_message": msg,
                "final_action": "send",
                "rationale": "Merchant expressed interest — proceeding with action flow",
            }
        return {
            "final_action": "send",
            "final_body": "Let me get the details for you. Stand by.",
            "final_cta": "open_ended",
            "rationale": "Merchant expressed interest (no context loaded yet)",
        }

    # -----------------------------------------------------------------------
    # Node: handle_auto_reply  (suppress)
    # -----------------------------------------------------------------------
    def handle_auto_reply(state: ReplyGraphState) -> ReplyGraphState:
        conv_id = state.get("conversation_id", "")
        conv_state = state_manager.get_state(conv_id)
        if conv_state:
            conv_state.nudge_count += 1
            state_manager.repository.save(conv_state)
            nudge = conv_state.nudge_count
        else:
            nudge = 1
            
        if nudge == 1:
            return {
                "final_action": "send",
                "final_body": "Samajh gayi. Isse pehle, kya aap khud dekhna chahingi ki exact kya missing hai? 2 minute ka kaam hai.",
                "final_cta": "open_ended",
                "rationale": "Detected auto-reply, nudging once to re-engage",
            }
        else:
            return {
                "final_action": "end",
                "rationale": "Detected repeated auto-reply pattern, ending conversation gracefully",
            }

    # -----------------------------------------------------------------------
    # Node: handle_not_interested  (graceful_exit)
    # -----------------------------------------------------------------------
    def handle_not_interested(state: ReplyGraphState) -> ReplyGraphState:
        return {
            "final_action": "end",
            "rationale": "Merchant not interested — graceful exit",
        }

    # -----------------------------------------------------------------------
    # Node: handle_wait  (wait_and_retry)
    # -----------------------------------------------------------------------
    def handle_wait(state: ReplyGraphState) -> ReplyGraphState:
        return {
            "final_action": "wait",
            "wait_seconds": 3600,
            "rationale": "Merchant said 'not now' — will retry in 1 hour",
        }

    # -----------------------------------------------------------------------
    # Node: handle_question  (answer_question)
    # -----------------------------------------------------------------------
    def handle_question(state: ReplyGraphState) -> ReplyGraphState:
        mid = state.get("merchant_id", "")
        conv_state = state_manager.get_state(state.get("conversation_id", ""))
        current_opp_str = conv_state.current_opportunity if conv_state else None

        try:
            opp_type = OpportunityType(current_opp_str) if current_opp_str else OpportunityType.INFORMATIONAL_OPPORTUNITY
        except ValueError:
            opp_type = OpportunityType.INFORMATIONAL_OPPORTUNITY

        norm_ctx = context_store.get(f"merchant:{mid}") or context_store.get("normalized")
        if norm_ctx:
            grounded = retriever.retrieve_for_opportunity(norm_ctx, opp_type)
            msg = composer.compose(grounded, "open_ended", opp_type.value)
            return {
                "grounded_context": grounded,
                "composed_message": msg,
                "final_action": "send",
                "rationale": "Answering merchant question with grounded context",
            }
        return {
            "final_action": "send",
            "final_body": "I'll look into that and get back to you shortly.",
            "final_cta": "open_ended",
            "rationale": "Answering merchant question (no context loaded yet)",
        }

    # -----------------------------------------------------------------------
    # Node: handle_curveball  (polite_redirect)
    # -----------------------------------------------------------------------
    def handle_curveball(state: ReplyGraphState) -> ReplyGraphState:
        return {
            "final_action": "send",
            "final_body": (
                "I'll leave that to your specialist — it's outside what I can help with. "
                "Coming back to the main topic, want me to proceed?"
            ),
            "final_cta": "open_ended",
            "rationale": "Off-topic question — polite redirect",
        }

    # -----------------------------------------------------------------------
    # Node: handle_ambiguous  (clarify)
    # -----------------------------------------------------------------------
    def handle_ambiguous(state: ReplyGraphState) -> ReplyGraphState:
        return {
            "final_action": "send",
            "final_body": "Not sure I caught that — could you clarify? Are you interested in proceeding?",
            "final_cta": "binary_yes_stop",
            "rationale": "Ambiguous response — requesting clarification",
        }

    # -----------------------------------------------------------------------
    # Node: compose_final
    # Fills final_body/cta from composed_message if not already set.
    # -----------------------------------------------------------------------
    def compose_final(state: ReplyGraphState) -> ReplyGraphState:
        updates: ReplyGraphState = {}
        msg = state.get("composed_message")
        if msg and not state.get("final_body"):
            updates["final_body"] = msg.body
            updates["final_cta"] = msg.cta
        return updates

    # -----------------------------------------------------------------------
    # Node: validate_message
    # Runs validation; repairs if failed; does NOT bypass grounding.
    # -----------------------------------------------------------------------
    def validate_message(state: ReplyGraphState) -> ReplyGraphState:
        grounded = state.get("grounded_context")
        msg = state.get("composed_message")
        if not grounded or not msg:
            return {}

        conv_state = state_manager.get_state(state.get("conversation_id", ""))
        history = [m.get("body", "") for m in conv_state.message_history] if conv_state else []

        expected_cta = state.get("final_cta") or msg.cta
        result = validator.validate(msg, grounded, history, expected_cta)

        updates: ReplyGraphState = {"validation_result": result}
        if not result.valid:
            repaired = validator.repair(msg, grounded, expected_cta)
            updates["composed_message"] = repaired
            updates["final_body"] = repaired.body
            updates["final_cta"] = repaired.cta
        else:
            updates["final_body"] = msg.body
            updates["final_cta"] = msg.cta

        return updates

    # -----------------------------------------------------------------------
    # Node: update_conversation
    # Persists result to state store and suppression engine.
    # -----------------------------------------------------------------------
    def update_conversation(state: ReplyGraphState) -> ReplyGraphState:
        conv_id = state.get("conversation_id", "")
        final_action = state.get("final_action", "send")
        final_body = state.get("final_body", "")
        intent_str = state.get("intent")

        conv_state = state_manager.get_state(conv_id)
        if conv_state:
            if final_body:
                state_manager.add_message(conv_id, "vera", final_body, intent_str)
            if intent_str:
                updates = {"intent": intent_str, "last_message": final_body, "last_action": final_action}
                if intent_str == "auto_reply":
                    updates["nudge_count"] = conv_state.nudge_count + 1
                state_manager.update_state(conv_id, **updates)
            else:
                state_manager.update_state(conv_id, last_message=final_body, last_action=final_action)

            # Update engagement state based on action
            if final_action == "end":
                state_manager.update_state(conv_id, engagement_state=EngagementState.ENDED)
            elif final_action == "wait":
                state_manager.update_state(conv_id, engagement_state=EngagementState.WAITING)
            else:
                state_manager.update_state(conv_id, engagement_state=EngagementState.ACTIVE)

            # Record to suppression if we're handling an active opportunity
            if conv_state.current_opportunity and final_action == "send" and final_body:
                suppression.record_response(
                    state.get("merchant_id", ""),
                    "",
                    conv_state.current_opportunity,
                    state.get("incoming_message", ""),
                )

        return {}

    # -----------------------------------------------------------------------
    # Routing function
    # -----------------------------------------------------------------------
    def route_intent(state: ReplyGraphState) -> str:
        route = state.get("route", "clarify")
        # Map route → node name
        valid_routes = {
            "action_flow",
            "suppress",
            "graceful_exit",
            "wait_and_retry",
            "answer_question",
            "polite_redirect",
            "clarify",
        }
        return route if route in valid_routes else "clarify"

    # -----------------------------------------------------------------------
    # Build graph
    # -----------------------------------------------------------------------
    graph = StateGraph(ReplyGraphState)

    # Nodes
    graph.add_node("load_state", load_state)
    graph.add_node("analyze_intent", analyze_intent)
    graph.add_node("handle_interested", handle_interested)
    graph.add_node("handle_auto_reply", handle_auto_reply)
    graph.add_node("handle_not_interested", handle_not_interested)
    graph.add_node("handle_wait", handle_wait)
    graph.add_node("handle_question", handle_question)
    graph.add_node("handle_curveball", handle_curveball)
    graph.add_node("handle_ambiguous", handle_ambiguous)
    graph.add_node("compose_final", compose_final)
    graph.add_node("validate_message", validate_message)
    graph.add_node("update_conversation", update_conversation)

    # Edges
    graph.set_entry_point("load_state")
    graph.add_edge("load_state", "analyze_intent")

    graph.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {
            "action_flow": "handle_interested",
            "suppress": "handle_auto_reply",
            "graceful_exit": "handle_not_interested",
            "wait_and_retry": "handle_wait",
            "answer_question": "handle_question",
            "polite_redirect": "handle_curveball",
            "clarify": "handle_ambiguous",
        },
    )

    # Intent handlers that may compose
    graph.add_edge("handle_interested", "compose_final")
    graph.add_edge("handle_question", "compose_final")

    # Compose-final → validate
    graph.add_edge("compose_final", "validate_message")
    graph.add_edge("validate_message", "update_conversation")

    # Intent handlers that do NOT compose (directly go to update_conversation)
    graph.add_edge("handle_auto_reply", "update_conversation")
    graph.add_edge("handle_not_interested", "update_conversation")
    graph.add_edge("handle_wait", "update_conversation")
    graph.add_edge("handle_curveball", "update_conversation")
    graph.add_edge("handle_ambiguous", "update_conversation")

    graph.add_edge("update_conversation", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Entry point used by main.py
# ---------------------------------------------------------------------------

def process_reply(
    conversation_id: str,
    merchant_id: str,
    message: str,
    turn_number: int,
    graph,
    context_store: Dict,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the reply graph and return a response dict for main.py."""

    initial_state: ReplyGraphState = {
        "conversation_id": conversation_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "incoming_message": message,
        "intent": None,
        "route": "",
        "grounded_context": None,
        "composed_message": None,
        "validation_result": None,
        "final_action": "send",
        "final_body": "",
        "final_cta": "open_ended",
        "rationale": "",
        "wait_seconds": 0,
    }

    result = graph.invoke(initial_state)

    response: Dict[str, Any] = {
        "action": result.get("final_action", "send"),
        "body": result.get("final_body") or None,
        "cta": result.get("final_cta") or None,
        "rationale": result.get("rationale", ""),
    }

    if result.get("final_action") == "wait":
        response["wait_seconds"] = result.get("wait_seconds", 3600)

    return response