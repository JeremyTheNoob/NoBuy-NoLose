import os
import yaml
from pathlib import Path
from pydantic import BaseModel


class TushareConfig(BaseModel):
    token: str = ""

class CustomApiConfig(BaseModel):
    url: str = "http://localhost:8001"
    api_key: str = ""

class DataConfig(BaseModel):
    provider_order: list[str] = ["tushare", "akshare", "sina", "eastmoney"]
    tushare: TushareConfig = TushareConfig()
    custom_api: CustomApiConfig = CustomApiConfig()
    cache_ttl: int = 3600

class ProviderConfig(BaseModel):
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    host: str = "http://localhost:11434"

class AIConfig(BaseModel):
    provider: str = "none"
    deepseek: ProviderConfig = ProviderConfig(model="deepseek-chat", base_url="https://api.deepseek.com/v1")
    qwen: ProviderConfig = ProviderConfig(model="qwen-plus", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    zhipu: ProviderConfig = ProviderConfig(model="glm-4-flash", base_url="https://open.bigmodel.cn/api/paas/v4")
    moonshot: ProviderConfig = ProviderConfig(model="moonshot-v1-8k", base_url="https://api.moonshot.cn/v1")
    ollama: ProviderConfig = ProviderConfig(model="qwen2.5:7b")
    openai: ProviderConfig = ProviderConfig(model="gpt-4o", base_url="https://api.openai.com/v1")
    custom: ProviderConfig = ProviderConfig()

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

class AppConfig(BaseModel):
    data: DataConfig = DataConfig()
    ai: AIConfig = AIConfig()
    server: ServerConfig = ServerConfig()


def load_config(config_path: str | None = None) -> AppConfig:
    if config_path is None:
        config_path = os.environ.get("MT_CONFIG", "config.yaml")

    if not Path(config_path).exists():
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return AppConfig(**raw)
