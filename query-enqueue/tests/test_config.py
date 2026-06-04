import pytest

from query_enqueue.config import EnqueueConfig, ConfigError, ModelTarget
from query_enqueue.providers import Provider, ProviderRegistry


def write_config(tmp_path, text):
    path = tmp_path / "enqueue.yaml"
    path.write_text(text)
    return path


def registry(*names):
    return ProviderRegistry(
        providers={n: Provider(name=n, type=n) for n in names}
    )


RICH = (
    "models:\n"
    "  - name: claude-opus-4-8\n"
    "    provider: anthropic\n"
    "    max_tokens: 1024\n"
    "    temperature: 0.7\n"
    "  - name: llama3.1:8b\n"
    "    provider: local\n"
)


def test_load_parses_model_targets(tmp_path):
    cfg = EnqueueConfig.load(write_config(tmp_path, RICH), registry("anthropic", "local"))
    opus, llama = cfg.models
    assert opus.name == "claude-opus-4-8"
    assert opus.provider == "anthropic"
    assert opus.options == {"max_tokens": 1024, "temperature": 0.7}
    assert llama.name == "llama3.1:8b"
    assert llama.provider == "local"
    assert llama.options == {}


def test_to_dict_emits_provider_name_then_options():
    model = ModelTarget(name="claude-opus-4-8", provider="anthropic", options={"max_tokens": 1024})
    assert model.to_dict() == {
        "provider": "anthropic",
        "name": "claude-opus-4-8",
        "max_tokens": 1024,
    }


def test_unknown_provider_reference_raises(tmp_path):
    text = "models:\n  - name: m\n    provider: nope\n"
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, text), registry("anthropic"))


def test_model_requires_provider(tmp_path):
    text = "models:\n  - name: m\n"
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, text), registry("anthropic"))


def test_model_requires_name(tmp_path):
    text = "models:\n  - provider: anthropic\n"
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, text), registry("anthropic"))


def test_string_shorthand_is_rejected(tmp_path):
    text = "models:\n  - claude-opus-4-8\n"
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, text), registry("anthropic"))


def test_ignore_defaults_to_empty(tmp_path):
    text = "models:\n  - name: m\n    provider: anthropic\n"
    cfg = EnqueueConfig.load(write_config(tmp_path, text), registry("anthropic"))
    assert cfg.ignore == []


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        EnqueueConfig.load(tmp_path / "nope.yaml", registry("anthropic"))


def test_empty_models_raises(tmp_path):
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, "models: []\n"), registry("anthropic"))


def test_models_must_be_a_list(tmp_path):
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, "models: x\n"), registry("anthropic"))


def test_ignore_must_be_a_list(tmp_path):
    text = "models:\n  - name: m\n    provider: anthropic\nignore: x\n"
    with pytest.raises(ConfigError):
        EnqueueConfig.load(write_config(tmp_path, text), registry("anthropic"))
