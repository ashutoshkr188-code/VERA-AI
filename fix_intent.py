with open('app/main.py', 'r') as f:
    content = f.read()
content = content.replace('msg_lower = body.message.lower().strip()', 'msg_lower = (body.message or "").lower().strip()')
with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')