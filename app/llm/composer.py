from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.category import CategoryContext
from app.models.merchant import MerchantContext
from app.models.trigger import TriggerContext
from app.models.customer import CustomerContext
from app.core.opportunity_engine import Opportunity, OpportunityType
from app.retrieval.structured_retriever import GroundedContext
from app.llm.ollama_client import OllamaProvider

FROM_SYSTEM_PROMPT = """You are Vera, a merchant-facing AI assistant. You compose WhatsApp messages for Merchants (Indian businesses). Never invent facts. Only use provided facts. Be concise. Return STRICT JSON: {"body": str, "cta": str}"""

class MessageCompose(BaseModel):
    body: str
    cta: str
    rationale: str = ""
    claims: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body": self.body,
            "cta": self.cta,
            "rationale": self.rationale,
            "claims": self.claims
        }

class Composer:
    def __init__(self, llm_provider: Any):
        self.llm = llm_provider
    
    def compose(self, grounded: GroundedContext, cta_instruction: str = "open_ended", opportunity_type: str = "") -> MessageCompose:
        system_prompt = FROM_SYSTEM_PROMPT
        facts_text = "\n".join([f"- {f.text}" for f in grounded.facts])
        
        user_prompt = f"""Compose a WhatsApp message using ONLY these facts:
{facts_text}

Trigger: {grounded.trigger.kind}
Opportunity: {opportunity_type}
CTA Type: {cta_instruction}

JSON output format: {{"body": "...", "cta": "..."}}"""
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.0,
                max_tokens=200
            )
            
            # Parse JSON response
            import json
            if response.startswith("```json"): response = response[7:]
            elif response.startswith("```"): response = response[3:]
            if response.endswith("```"): response = response[:-3]
            data = json.loads(response.strip())
            
            return MessageCompose(
                body=data.get("body", ""),
                cta=data.get("cta", cta_instruction),
                rationale="LLM composition successful",
                claims=[]
            )
        except Exception as e:
            # Fallback to deterministic composition
            return self._fallback_compose(grounded, cta_instruction, opportunity_type)
    
    def _fallback_compose(self, grounded: GroundedContext, cta_instruction: str, opportunity_type: str) -> MessageCompose:
        m = grounded.merchant
        c = grounded.category
        t = grounded.trigger
        
        owner_name = m.identity.owner_first_name or m.identity.name
        
        if opportunity_type == "research_digest":
            fact_texts = [f.text for f in grounded.facts if "digest" in f.fact_id or "trial" in f.fact_id]
            main_fact = fact_texts[0] if fact_texts else "New research available"
            body = f"{owner_name}, {main_fact}. Worth a look. Want me to share details?"
            rationale = "Research digest with grounded fact"
        elif opportunity_type == "perf_dip":
            ctr_fact = next((f.text for f in grounded.facts if "ctr" in f.fact_id.lower()), "CTR has dipped")
            body = f"{owner_name}, your {ctr_fact.lower()}. Want me to check what's driving this?"
            rationale = "Performance dip alert with grounded metric"
        elif opportunity_type == "recall_due":
            cust = grounded.customer
            patient_name = cust.identity.name if cust else "Patient"
            body = f"Hi {patient_name}, your recall is due. Want to book?"
            rationale = "Recall reminder"
        else:
            body = f"{owner_name}, checking in on your {c.slug} business. How can I help?"
            rationale = "General check-in"
        
        return MessageCompose(
            body=body,
            cta=cta_instruction,
            rationale=rationale,
            claims=[]
        )