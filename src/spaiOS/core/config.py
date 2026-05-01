import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OllamaConfig:
    model: str = "llama3.2:3b"
    vision_model: str = "moondream:latest"
    host: str = "http://localhost:11434"


@dataclass
class AnthropicConfig:
    api_key: str = ""
    model: str = "claude-haiku-4-5-20251001"


@dataclass
class OpenAIConfig:
    api_key: str = ""
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"


@dataclass
class AppConfig:
    provider: str = "ollama"
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)


def _find_config() -> Path | None:
    candidates = [
        Path.cwd() / "config.toml",
        Path.home() / ".config" / "spaiOS" / "config.toml",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def load_config() -> AppConfig:
    path = _find_config()
    if path is None:
        return AppConfig()

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    cfg = AppConfig()
    cfg.provider = raw.get("provider", {}).get("name", "ollama")

    if "ollama" in raw:
        o = raw["ollama"]
        cfg.ollama = OllamaConfig(
            model=o.get("model", cfg.ollama.model),
            vision_model=o.get("vision_model", cfg.ollama.vision_model),
            host=o.get("host", cfg.ollama.host),
        )

    if "anthropic" in raw:
        a = raw["anthropic"]
        cfg.anthropic = AnthropicConfig(
            api_key=a.get("api_key", ""),
            model=a.get("model", cfg.anthropic.model),
        )

    if "openai" in raw:
        o = raw["openai"]
        cfg.openai = OpenAIConfig(
            api_key=o.get("api_key", ""),
            model=o.get("model", cfg.openai.model),
            base_url=o.get("base_url", cfg.openai.base_url),
        )

    return cfg
