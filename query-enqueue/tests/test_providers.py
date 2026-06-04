import pytest

from query_enqueue.providers import Auth, Provider, ProviderError, ProviderRegistry


def write_registry(tmp_path, text):
    path = tmp_path / "providers.yaml"
    path.write_text(text)
    return path


REGISTRY = (
    "providers:\n"
    "  anthropic:\n"
    "    type: anthropic\n"
    "    base_url: https://api.anthropic.com\n"
    "    auth: {type: env, var: ANTHROPIC_API_KEY}\n"
    "  local:\n"
    "    type: openai\n"
    "    base_url: http://localhost:11434/v1\n"
    "    auth: {type: none}\n"
    "  bedrock:\n"
    "    region: us-east-1\n"
    "    auth: {type: aws, profile: default}\n"
)


def test_load_parses_providers(tmp_path):
    reg = ProviderRegistry.load(write_registry(tmp_path, REGISTRY))
    assert set(reg.providers) == {"anthropic", "local", "bedrock"}
    anthropic = reg.get("anthropic")
    assert anthropic.name == "anthropic"
    assert anthropic.type == "anthropic"
    assert anthropic.base_url == "https://api.anthropic.com"
    assert anthropic.auth == Auth(type="env", params={"var": "ANTHROPIC_API_KEY"})


def test_type_defaults_to_key(tmp_path):
    reg = ProviderRegistry.load(write_registry(tmp_path, REGISTRY))
    assert reg.get("bedrock").type == "bedrock"
    assert reg.get("bedrock").region == "us-east-1"
    assert reg.get("bedrock").auth == Auth(type="aws", params={"profile": "default"})


def test_unknown_keys_become_options(tmp_path):
    reg = ProviderRegistry.load(
        write_registry(
            tmp_path,
            "providers:\n  x:\n    type: openai\n    organization: org-123\n",
        )
    )
    assert reg.get("x").options == {"organization": "org-123"}


def test_contains_and_missing_get(tmp_path):
    reg = ProviderRegistry.load(write_registry(tmp_path, REGISTRY))
    assert "local" in reg
    assert "nope" not in reg
    with pytest.raises(ProviderError):
        reg.get("nope")


def test_auth_defaults_to_none_when_omitted(tmp_path):
    reg = ProviderRegistry.load(
        write_registry(tmp_path, "providers:\n  x:\n    type: openai\n")
    )
    assert reg.get("x").auth == Auth(type="none", params={})


def test_missing_file_raises(tmp_path):
    with pytest.raises(ProviderError):
        ProviderRegistry.load(tmp_path / "nope.yaml")


def test_missing_providers_key_raises(tmp_path):
    with pytest.raises(ProviderError):
        ProviderRegistry.load(write_registry(tmp_path, "other: 1\n"))


def test_env_auth_requires_var(tmp_path):
    with pytest.raises(ProviderError):
        ProviderRegistry.load(
            write_registry(tmp_path, "providers:\n  x:\n    auth: {type: env}\n")
        )


def test_unknown_auth_type_raises(tmp_path):
    with pytest.raises(ProviderError):
        ProviderRegistry.load(
            write_registry(tmp_path, "providers:\n  x:\n    auth: {type: magic}\n")
        )


def test_provider_must_be_mapping(tmp_path):
    with pytest.raises(ProviderError):
        ProviderRegistry.load(write_registry(tmp_path, "providers:\n  x: just-a-string\n"))
