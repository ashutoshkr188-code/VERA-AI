with open('judge_simulator.py', 'r') as f:
    content = f.read()
content = content.replace('LLM_PROVIDER = "openai"', 'LLM_PROVIDER = "ollama"')
content = content.replace('LLM_API_KEY = ""', 'LLM_API_KEY = ""')
content = content.replace('LLM_MODEL = ""', 'LLM_MODEL = "llama3.1:8b"')
with open('judge_simulator.py', 'w') as f:
    f.write(content)
print('Fixed')