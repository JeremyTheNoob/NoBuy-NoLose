import json
import httpx
from openai import OpenAI
from .base import AIAdapter, build_prompt
from ..config import AppConfig


class OllamaAdapter(AIAdapter):
    name = "ollama"

    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.host = host
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = httpx.get(f"{self.host}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> list[dict]:
        prompt = build_prompt(reasons, stock_name, symbol)
        try:
            resp = httpx.post(
                f"{self.host}/api/chat",
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "stream": False},
                timeout=120,
            )
            content = resp.json()["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            enhanced = json.loads(content)
            if isinstance(enhanced, list):
                return enhanced
        except Exception:
            pass
        return reasons


class OpenAICompatAdapter(AIAdapter):
    """通用 OpenAI 兼容接口适配器"""

    def __init__(self, name: str, api_key: str, model: str, base_url: str):
        self._name = name
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return bool(self.api_key)

    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> list[dict]:
        if not self.client:
            return reasons
        prompt = build_prompt(reasons, stock_name, symbol)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            content = resp.choices[0].message.content or ""
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            enhanced = json.loads(content)
            if isinstance(enhanced, list):
                return enhanced
        except Exception:
            pass
        return reasons


def build_ai_adapter(config: AppConfig) -> AIAdapter | None:
    """根据配置创建 AI 适配器，返回 None 表示禁用"""
    ai = config.ai
    if ai.provider == "none" or not ai.provider:
        return None

    if ai.provider == "ollama":
        return OllamaAdapter(host=ai.ollama.host, model=ai.ollama.model)

    providers = {
        "deepseek": ai.deepseek,
        "qwen": ai.qwen,
        "zhipu": ai.zhipu,
        "moonshot": ai.moonshot,
        "openai": ai.openai,
    }

    if ai.provider in providers:
        cfg = providers[ai.provider]
        if cfg.api_key and cfg.model:
            return OpenAICompatAdapter(ai.provider, cfg.api_key, cfg.model, cfg.base_url)
        return None

    if ai.provider == "custom":
        if ai.custom.api_key and ai.custom.base_url:
            return OpenAICompatAdapter("custom", ai.custom.api_key, ai.custom.model, ai.custom.base_url)
        return None

    return None
