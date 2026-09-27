with open('app/main.py', 'r') as f:
    content = f.read()

old_call = '''        opportunity = opportunity_engine.select_best_opportunity(normalized, signals, suppression)'''
new_call = '''        opportunity = opportunity_engine.select_best_opportunity(normalized, signals, suppression, trigger.get("kind"))'''

content = content.replace(old_call, new_call)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')