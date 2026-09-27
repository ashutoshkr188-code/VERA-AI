with open('judge_simulator.py', 'r') as f:
    content = f.read()
content = content.replace('TEST_SCENARIO = "all"', 'TEST_SCENARIO = "full"')
with open('judge_simulator.py', 'w') as f:
    f.write(content)
print('Fixed')