with open('app/main.py', 'r') as f:
    content = f.read()

# Fix the key format to use string values instead of enum representations
old_key = '''    key = f"{scope}:{context_id}"'''
new_key = '''    # Use string value of scope for consistent key format
    scope_str = scope.value if hasattr(scope, 'value') else str(scope)
    key = f"{scope_str}:{context_id}"'''

content = content.replace(old_key, new_key)

# Also fix the merchant_key, category_key, trigger_key in context push
old_merchant_key = '''        merchant_key = f"merchant:{merchant_id}"'''
new_merchant_key = '''        merchant_key = f"merchant:{merchant_id}"'''

content = content.replace(old_merchant_key, new_merchant_key)

old_category_key = '''        category_key = f"category:{category_slug}"'''
new_category_key = '''        category_key = f"category:{category_slug}"'''

content = content.replace(old_category_key, new_category_key)

old_trigger_key = '''        trigger_key = f"trigger:{trigger_id}"'''
new_trigger_key = '''        trigger_key = f"trigger:{trigger_id}"'''

content = content.replace(old_trigger_key, new_trigger_key)

# Fix the context_store.get and context_store[] in tick endpoint
old_get = '''        normalized = context_store.get(merchant_id)'''
new_get = '''        normalized = context_store.get(f"merchant:{merchant_id}")'''

content = content.replace(old_get, new_get)

old_store = '''            context_store[merchant_id] = normalized'''
new_store = '''            context_store[f"merchant:{merchant_id}"] = normalized'''

content = content.replace(old_store, new_store)

old_store2 = '''            context_store["normalized"] = normalized'''
new_store2 = '''            context_store["normalized"] = normalized'''

content = content.replace(old_store2, new_store2)

# Fix the trigger_key in tick endpoint
old_trigger_key2 = '''        trigger_key = f"trigger:{trigger_id}"'''
new_trigger_key2 = '''        trigger_key = f"trigger:{trigger_id}"'''

content = content.replace(old_trigger_key2, new_trigger_key2)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')