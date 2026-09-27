# magicpin AI Challenge - Implementation Notes

## Challenge Requirements Summary

### Core Objective
Build an AI merchant engagement assistant (Vera) that sends highly specific, context-grounded, engaging messages to merchants on WhatsApp. The system must generalize to hidden context injections and not overfit canonical test cases.

### 4-Context Framework
Every message is composed from:
1. CategoryContext - Slow-changing vertical knowledge (voice, offer catalog, peer stats, digest, trends)
2. MerchantContext - Specific business state (identity, subscription, performance, offers, history, signals)
3. TriggerContext - Event prompting the message (external/internal, urgency, suppression_key, expires_at)
4. CustomerContext (optional) - Customer state for customer-facing messages

### API Endpoints (5 required)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /v1/healthz | GET | Liveness probe, returns contexts_loaded counts |
| /v1/metadata | GET | Bot identity (team, model, approach) |
| /v1/context | POST | Receive context pushes (idempotent by scope+context_id+version) |
| /v1/tick | POST | Bot initiates proactive messages based on available triggers |
| /v1/reply | POST | Handle merchant/customer replies (returns send/wait/end) |

### Evaluation Dimensions (5 x 10 = 50 max)
1. Specificity - Verifiable facts (numbers, dates, sources, concrete claims)
2. Category Fit - Voice, vocabulary, taboos match the vertical
3. Merchant Fit - Personalized to specific merchant (name, data, language)
4. Trigger Relevance - Clear why now connection to the trigger
5. Engagement Compulsion - Uses levers: specificity, loss aversion, social proof, effort externalization, curiosity, reciprocity, asking merchant, single binary CTA

### Constraints & Rules
- WhatsApp 24h session: First outbound uses template; subsequent within 24h of reply can be free-form
- Single primary CTA: Binary YES/STOP for action triggers; no CTA for pure info
- No fabrication: Never invent facts, prices, dates, offers, statistics, customer behavior, peer comparisons
- Voice match: Peer/colleague tone, not promotional; technical vocab OK if category allows
- Hindi-English code-mix: When merchant language preference supports it
- Deterministic: Same input -> materially consistent output (temperature=0)
- Timeout: 30s per call
- No URLs in body: Meta would reject

### Anti-patterns (penalized)
- Generic offers (Flat 30% off) when service+price available (Haircut @ Rs.99)
- Multiple CTAs in one message
- Buried CTA
- Promotional tone for clinical categories
- Hallucinated data
- Long preambles (Hope you are doing well)
- Re-introducing after first message
- Ignoring language preference
- Repetition (same body verbatim)

### Hidden Context Injection (Post-submission)
Judge injects after submission:
- New digest items in category contexts
- Updated performance snapshots
- New triggers
- Customer contexts for 5 of 30 test pairs

### Replay Test (Top 10)
3 scenarios:
1. Auto-reply hell (4 identical canned replies)
2. Intent transition (merchant says lets do it after qualification)
3. Hostile/off-topic (abuse + unrelated question)

### Dataset Structure
dataset/
|-- categories/ (5 files: dentists, salons, restaurants, gyms, pharmacies)
|-- merchants_seed.json (10 seeds -> expands to 50)
|-- customers_seed.json (15 seeds -> expands to 200)
|-- triggers_seed.json (25 seeds -> expands to 100)
|-- generate_dataset.py (deterministic expansion, seed=20260426)

### Canonical Test Pairs
30 specific (merchant, trigger) pairs in test_pairs.json that all candidates must produce messages for.

### Context Payload Schemas
See challenge-testing-brief.md section 3 for exact JSON schemas for each scope.

### Judge Simulator
judge_simulator.py - runs local evaluation against bot endpoint. Requires LLM_API_KEY for scoring.
