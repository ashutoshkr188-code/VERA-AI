with open('judge_simulator.py', 'r') as f:
    content = f.read()
content = content.replace('TEST_SCENARIO = "full"', 'TEST_SCENARIO = "full_evaluation"')
with open('judge_simulator.py', 'w') as f:
    f.write(content)
print('Fixed')