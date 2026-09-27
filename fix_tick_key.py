with open('app/main.py', 'r') as f:
    content = f.read()

# Fix the tick endpoint to define merchant_key before using it
old_code = '''        normalized = context_store.get(f"merchant:{merchant_id}")
        if not normalized:
            category_slug = raw_contexts.get(f"merchant:{merchant_id}", {}).get("category_slug")
            if category_slug:
                category_key = f"category:{category_slug}"
                if category_key in raw_contexts:
                    normalized = normalizer.normalize(
                        category=raw_contexts[category_key],
                        merchant=raw_contexts[merchant_key],'''

new_code = '''        normalized = context_store.get(f"merchant:{merchant_id}")
        if not normalized:
            merchant_key = f"merchant:{merchant_id}"
            category_slug = raw_contexts.get(merchant_key, {}).get("category_slug")
            if category_slug:
                category_key = f"category:{category_slug}"
                if category_key in raw_contexts:
                    normalized = normalizer.normalize(
                        category=raw_contexts[category_key],
                        merchant=raw_contexts[merchant_key],'''

content = content.replace(old_code, new_code)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')