with open('app/main.py', 'r') as f:
    content = f.read()

# Find the tick endpoint
import re
match = re.search(r'@app\.post\("/v1/tick"\).*?(?=@app\.post|@app\.get|if __name__)', content, re.DOTALL)
if match:
    with open('tick_endpoint.txt', 'w') as f:
        f.write(match.group(0))
    print('Written to tick_endpoint.txt')
else:
    print('Not found')