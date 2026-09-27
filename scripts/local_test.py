#!/usr/bin/env python3
"""
Local test script to verify the bot works with the judge simulator.
Run this before submitting to ensure basic functionality.
"""
import json
import sys
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config.settings import settings
from app.context.normalizer import ContextNormalizer
from app.context.fact_ledger import fact_ledger
from app.core.signal_extractor import SignalExtractor
from app.core.opportunity_engine import OpportunityEngine
from app.core.suppression import SuppressionEngine
from app.core.cta_engine import CTAEngine
from app.retrieval.structured_retriever import StructuredRetriever
from app.llm.ollama_client import OllamaProvider
from app.llm.composer import Composer
from app.validation.validator import Validator

def test_components():
    print("Testing components...")
    
    # Test normalizer
    print("\n1. Testing ContextNormalizer...")
    normalizer = ContextNormalizer()
    
    # Load test data
    dataset_dir = Path(__file__).parent.parent / "dataset"
    
    with open(dataset_dir / "categories" / "dentists.json") as f:
        category = json.load(f)
    
    with open(dataset_dir / "merchants_seed.json") as f:
        merchants = json.load(f)["merchants"]
        merchant = merchants[0]  # Dr. Meera
    
    with open(dataset_dir / "triggers_seed.json") as f:
        triggers = json.load(f)["triggers"]
        trigger = triggers[0]  # research_digest
    
    normalized = normalizer.normalize(category, merchant, trigger)
    print(f"   Normalized: category={normalized.category.slug}, merchant={normalized.merchant.merchant_id}, trigger={normalized.trigger.kind}")
    
    # Test fact ledger
    print("\n2. Testing FactLedger...")
    fact_ledger.extract_from_context(normalized)
    facts = fact_ledger.get_verified_facts()
    print(f"   Extracted {len(facts)} verified facts")
    for f in facts[:3]:
        print(f"   - {f.fact_id}: {f.text[:60]}...")
    
    # Test signal extractor
    print("\n3. Testing SignalExtractor...")
    signal_extractor = SignalExtractor()
    signals = signal_extractor.extract_signals(normalized)
    print(f"   Extracted {len(signals)} signals")
    for s in signals:
        print(f"   - {s.type}: priority={s.priority}, urgency={s.urgency}")
    
    # Test opportunity engine
    print("\n4. Testing OpportunityEngine...")
    opp_engine = OpportunityEngine()
    suppression = SuppressionEngine()
    opportunity = opp_engine.select_best_opportunity(normalized, signals, suppression)
    print(f"   Selected opportunity: {opportunity.value if opportunity else 'None'}")
    
    # Test retriever
    print("\n5. Testing StructuredRetriever...")
    retriever = StructuredRetriever()
    if opportunity:
        grounded = retriever.retrieve_for_opportunity(normalized, opportunity)
        print(f"   Retrieved {len(grounded.facts)} grounded facts")
        print(f"   Rationale: {grounded.rationale}")
    
    # Test CTA engine
    print("\n6. Testing CTAEngine...")
    cta_engine = CTAEngine()
    cta = cta_engine.select_cta(opportunity, "merchant")
    print(f"   Selected CTA: {cta.value}")
    
    # Test Ollama provider (if available)
    print("\n7. Testing OllamaProvider...")
    llm = OllamaProvider()
    healthy = llm.health()
    print(f"   Ollama health: {healthy}")
    if healthy:
        models = llm.model_info()
        print(f"   Available models: {models.get('models', [])}")
    
    print("\n[OK] All component tests passed!")

def test_api():
    print("\n\nTesting API endpoints...")
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Health check
    resp = client.get("/v1/healthz")
    print(f"   /v1/healthz: {resp.status_code} - {resp.json()}")
    
    # Metadata
    resp = client.get("/v1/metadata")
    print(f"   /v1/metadata: {resp.status_code} - {resp.json()}")
    
    # Push context
    dataset_dir = Path(__file__).parent.parent / "dataset"
    
    with open(dataset_dir / "categories" / "dentists.json") as f:
        category = json.load(f)
    
    with open(dataset_dir / "merchants_seed.json") as f:
        merchants = json.load(f)["merchants"]
        merchant = merchants[0]
    
    with open(dataset_dir / "triggers_seed.json") as f:
        triggers = json.load(f)["triggers"]
        trigger = triggers[0]
    
    # Push category
    resp = client.post("/v1/context", json={
        "scope": "category",
        "context_id": category["slug"],
        "version": 1,
        "payload": category,
        "delivered_at": "2026-04-26T10:00:00Z"
    })
    print(f"   Push category: {resp.status_code} - {resp.json()}")
    
    # Push merchant
    resp = client.post("/v1/context", json={
        "scope": "merchant",
        "context_id": merchant["merchant_id"],
        "version": 1,
        "payload": merchant,
        "delivered_at": "2026-04-26T10:00:00Z"
    })
    print(f"   Push merchant: {resp.status_code} - {resp.json()}")
    
    # Push trigger
    resp = client.post("/v1/context", json={
        "scope": "trigger",
        "context_id": trigger["id"],
        "version": 1,
        "payload": trigger,
        "delivered_at": "2026-04-26T10:00:00Z"
    })
    print(f"   Push trigger: {resp.status_code} - {resp.json()}")
    
    # Tick
    resp = client.post("/v1/tick", json={
        "now": "2026-04-26T10:35:00Z",
        "available_triggers": [trigger["id"]]
    })
    print(f"   /v1/tick: {resp.status_code} - actions: {len(resp.json().get('actions', []))}")
    if resp.json().get('actions'):
        action = resp.json()['actions'][0]
        print(f"   Body: {action['body'][:100]}...")
        print(f"   CTA: {action['cta']}")
    
    print("\n[OK] API tests passed!")

if __name__ == "__main__":
    test_components()
    test_api()
    print("\n=== All tests passed! ===")