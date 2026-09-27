with open('app/core/signal_extractor.py', 'r') as f:
    content = f.read()
import re
matches = re.findall(r'(\w+)\s*=\s*"(\w+)', content)
print(matches[:20])