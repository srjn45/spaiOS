from spaiOS.core.config import AppConfig, load_config


def test_defaults_when_no_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.provider == "ollama"
    assert cfg.ollama.model == "llama3.2:3b"
    assert cfg.ollama.vision_model == "moondream:latest"
    assert cfg.anthropic.api_key == ""
    assert cfg.openai.api_key == ""


def test_provider_anthropic(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text(
        '[provider]\nname = "anthropic"\n\n'
        '[anthropic]\napi_key = "sk-ant-test"\nmodel = "claude-haiku-4-5-20251001"\n'
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.provider == "anthropic"
    assert cfg.anthropic.api_key == "sk-ant-test"
    assert cfg.anthropic.model == "claude-haiku-4-5-20251001"


def test_provider_openai(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text(
        '[provider]\nname = "openai"\n\n'
        '[openai]\napi_key = "sk-openai-test"\nmodel = "gpt-4o-mini"\n'
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.provider == "openai"
    assert cfg.openai.api_key == "sk-openai-test"
    assert cfg.openai.model == "gpt-4o-mini"


def test_ollama_custom_model(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text(
        '[provider]\nname = "ollama"\n\n[ollama]\nmodel = "llama3.1:8b"\n'
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.ollama.model == "llama3.1:8b"
    assert cfg.ollama.vision_model == "moondream:latest"


def test_missing_provider_section_defaults_to_ollama(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text('[ollama]\nmodel = "llama3.2:3b"\n')
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.provider == "ollama"


def test_openai_custom_base_url(tmp_path, monkeypatch):
    (tmp_path / "config.toml").write_text(
        '[provider]\nname = "openai"\n\n'
        '[openai]\napi_key = "x"\nbase_url = "https://custom.api/v1"\n'
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.openai.base_url == "https://custom.api/v1"


def test_app_config_is_dataclass():
    cfg = AppConfig()
    assert hasattr(cfg, "provider")
    assert hasattr(cfg, "ollama")
    assert hasattr(cfg, "anthropic")
    assert hasattr(cfg, "openai")
