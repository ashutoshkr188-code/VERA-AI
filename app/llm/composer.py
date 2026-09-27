from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.category import CategoryContext
from app.models.merchant import MerchantContext
from app.models.trigger import TriggerContext
from app.models.customer import CustomerContext
from app.core.opportunity_engine import Opportunity, OpportunityType
from app.retrieval.structured_retriever import GroundedContext
from app.llm.ollama_client import OllamaProvider

import threading
import time

LLM_SEMAPHORE = threading.Semaphore(1)

FROM_SYSTEM_PROMPT = "You are Vera. Write a short WhatsApp msg for this merchant based on facts. Return STRICT JSON: {\"body\": \"msg\", \"cta\": \"type\"}"

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
        if not LLM_SEMAPHORE.acquire(timeout=5.0):
            return self._fallback_compose(grounded, cta_instruction, opportunity_type)
            
        try:
            facts = " ".join([f.text for f in grounded.facts])
            owner = grounded.merchant.identity.owner_first_name or grounded.merchant.identity.name
            
            prompt = f"Merchant:{owner}, Category:{grounded.category.slug}, Trigger:{grounded.trigger.kind}, Opp:{opportunity_type}, Facts:{facts}, CTA:{cta_instruction}. Write JSON."
            
            response = self.llm.generate(
                prompt=prompt,
                system=FROM_SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=100
            )
            
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
        except Exception:
            return self._fallback_compose(grounded, cta_instruction, opportunity_type)
        finally:
            LLM_SEMAPHORE.release()
    
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