import os
import time
import requests

url = "http://localhost:8080/v1/tick"
payload = {
    "available_triggers": ["trig_welcome_1"],
    "window_start": "2023-10-01T00:00:00Z",
    "window_end": "2023-10-01T23:59:59Z"
}

# The context has to be setup before tick, but if we just want to hit OpenRouter directly, we can instantiate the provider and call generate!
from app.llm.ollama_client import HostedLLMProvider

def test_openrouter():
    os.environ["HOSTED_LLM_URL"] = "https://openrouter.ai/api/v1/chat/completions"
    os.environ["HOSTED_LLM_MODEL"] = "openrouter/free"
    # Ensure you set HOSTED_LLM_API_KEY in your shell before running this script
    api_key = os.environ.get("HOSTED_LLM_API_KEY")
    if api_key:
        os.environ["HOSTED_LLM_API_KEY"] = api_key
    
    provider = HostedLLMProvider()
    print("Testing OpenRouter...")
    start = time.time()
    try:
        response = provider.generate(
            prompt="Reply with exactly 'OK' formatted as JSON: {\"body\": \"OK\", \"cta\": \"open_ended\"}",
            system="You are a JSON assistant",
            temperature=0.0
        )
        latency = time.time() - start
        print(f"Success! Latency: {latency:.2f}s")
        print(f"Response: {response}")
    except Exception as e:
        latency = time.time() - start
        print(f"Failed after {latency:.2f}s: {e}")

if __name__ == "__main__":
    test_openrouter()
