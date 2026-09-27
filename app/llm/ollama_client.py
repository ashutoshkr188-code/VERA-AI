import os
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import httpx

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.0, max_tokens: int = 200) -> str:
        pass

    @abstractmethod
    def health(self) -> bool:
        pass

    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            self._client = httpx.Client(timeout=httpx.Timeout(15.0))
        return self._client
    
    def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.0, max_tokens: int = 200) -> str:
        client = self._get_client()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system:
            payload["system"] = system
        
        response = client.post(f"{self.base_url}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    
    def health(self) -> bool:
        try:
            client = self._get_client()
            response = client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def model_info(self) -> Dict[str, Any]:
        return {"model": self.model, "provider": "ollama"}

class HostedLLMProvider(LLMProvider):
    def __init__(self, base_url: str = None, model: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv("HOSTED_LLM_URL")
        self.model = model or os.getenv("HOSTED_LLM_MODEL")
        self.api_key = api_key or os.getenv("HOSTED_LLM_API_KEY")
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(15.0),
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
        return self._client
    
    def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.0, max_tokens: int = 200) -> str:
        if not self.base_url: return "{}"
        client = self._get_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        url = self.base_url
        if not url.endswith("/chat/completions"):
            url = f"{url.rstrip('/')}/chat/completions"
        
        # Adding OpenRouter specific headers (best effort)
        client = self._get_client()
        headers = client.headers.copy()
        headers["HTTP-Referer"] = "https://magicpin.in"
        headers["X-Title"] = "Vera AI Challenge"
        
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def health(self) -> bool:
        return bool(self.base_url)
    
    def model_info(self) -> Dict[str, Any]:
        return {"model": self.model, "provider": "hosted"}

def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider_type == "hosted":
        return HostedLLMProvider()
    return OllamaProvider()