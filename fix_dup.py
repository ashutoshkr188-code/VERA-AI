with open('app/core/signal_extractor.py', 'r') as f:
    content = f.read()
import re
pattern = r'(\w+)\s*=\s*"(\w+)"'
matches = list(re.finditer(pattern, content))
seen = set()
new_lines = []
lines = content.split('\n')
for line in lines:
    match = re.match(pattern, line.strip())
    if match:
        key = match.group(1)
        if key not in seen:
            seen.add(key)
            new_lines.append(line)
        else:
            print(f'Skipping duplicate: {key}')
    else:
        new_lines.append(line)
new_content = '\n'.join(new_lines)
with open('app/core/signal_extractor.py', 'w') as f:
    f.write(new_content)
print('Fixed duplicates')