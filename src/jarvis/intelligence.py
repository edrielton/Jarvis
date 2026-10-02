"""Provider boundary: core code never makes provider-specific HTTP calls."""
from __future__ import annotations

from abc import ABC, abstractmethod
import json
from urllib import error, request

from .configuration import Settings


class IntelligenceError(RuntimeError): pass
class ProviderConfigurationError(IntelligenceError): pass
class ModelUnavailableError(IntelligenceError): pass
class StructuredResponseError(IntelligenceError): pass


class IntelligenceProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...
    def understand(self, prompt: str) -> dict: return self.structured("understand", prompt)
    def plan(self, prompt: str) -> dict: return self.structured("plan", prompt)
    def review(self, prompt: str) -> dict: return self.structured("review", prompt)
    def repair(self, prompt: str) -> dict: return self.structured("repair", prompt)
    def summarize(self, prompt: str) -> dict: return self.structured("summarize", prompt)

    def structured(self, operation: str, prompt: str, attempts: int = 2) -> dict:
        request_prompt = f"Return ONLY a JSON object for {operation}.\n{prompt}"
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                raw = self.generate(request_prompt)
                candidate = raw.strip().removeprefix("```json").removesuffix("```").strip()
                parsed = json.loads(candidate)
                if not isinstance(parsed, dict): raise ValueError("JSON response is not an object")
                return parsed
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                request_prompt = "Your last response was invalid. Return ONLY one valid JSON object. " + prompt
        raise StructuredResponseError("Provider did not return valid structured JSON") from last_error


class NvidiaProvider(IntelligenceProvider):
    """Minimal OpenAI-compatible NVIDIA NIM client using only the stdlib."""
    def __init__(self, settings: Settings, timeout: int = 30) -> None:
        self.settings, self.timeout = settings, timeout

    def generate(self, prompt: str) -> str:
        if not self.settings.nvidia_api_key:
            raise ProviderConfigurationError("NVIDIA_API_KEY is not configured")
        if not self.settings.nvidia_model:
            raise ProviderConfigurationError("NVIDIA_MODEL is not configured")
        payload = json.dumps({"model": self.settings.nvidia_model, "messages": [{"role": "user", "content": prompt}]}).encode()
        req = request.Request(self.settings.nvidia_base_url + "/chat/completions", payload,
            headers={"Authorization": f"Bearer {self.settings.nvidia_api_key}", "Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                body = json.loads(response.read())
        except error.HTTPError as exc:
            if exc.code == 410: raise ModelUnavailableError("O modelo configurado não está mais disponível.") from exc
            if exc.code in {400,401,403,404,408,409,429,500,502,503,504}:
                raise IntelligenceError(f"NVIDIA API request failed with HTTP {exc.code}") from exc
            raise IntelligenceError("NVIDIA API request failed") from exc
        except (error.URLError, TimeoutError) as exc:
            raise IntelligenceError("NVIDIA API connectivity failure") from exc
        try: return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc: raise IntelligenceError("Unexpected NVIDIA API response") from exc
