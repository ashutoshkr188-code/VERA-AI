with open('app/main.py', 'r') as f:
    content = f.read()

# Fix the context push to get category_slug from merchant data when trigger is pushed
old_push = '''    # Try to build normalized context when we have merchant_id and category_slug
    if merchant_id and category_slug:
        merchant_key = f"merchant:{merchant_id}"
        category_key = f"category:{category_slug}"
        
        # Find trigger for this merchant
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
            
            fact_ledger.extract_from_context(normalized)
            normalized.facts = [f.fact_id for f in fact_ledger.get_verified_facts()]
            
            context_store[merchant_id] = normalized
            context_store["normalized"] = normalized'''

new_push = '''    # Try to build normalized context when we have merchant_id and category_slug
    # For trigger scope, get category_slug from merchant data
    if scope == "trigger" and merchant_id and not category_slug:
        merchant_key = f"merchant:{merchant_id}"
        if merchant_key in raw_contexts:
            category_slug = raw_contexts[merchant_key].get("category_slug")
    
    if merchant_id and category_slug:
        merchant_key = f"merchant:{merchant_id}"
        category_key = f"category:{category_slug}"
        
        # Find trigger for this merchant
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
            
            fact_ledger.extract_from_context(normalized)
            normalized.facts = [f.fact_id for f in fact_ledger.get_verified_facts()]
            
            context_store[merchant_id] = normalized
            context_store["normalized"] = normalized'''

content = content.replace(old_push, new_push)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')