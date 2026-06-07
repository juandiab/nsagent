from app.services.ai_provider_service import (
    normalize_azure_resource_endpoint,
    prepare_openai_chat_request,
    resolve_bedrock_openai_base,
)


def test_normalize_azure_resource_endpoint():
    assert (
        normalize_azure_resource_endpoint("https://my-resource.openai.azure.com")
        == "https://my-resource.openai.azure.com"
    )
    assert (
        normalize_azure_resource_endpoint("https://my-resource.openai.azure.com/openai/deployments/gpt-4o")
        == "https://my-resource.openai.azure.com"
    )


def test_resolve_bedrock_openai_base():
    assert resolve_bedrock_openai_base("us-east-1") == (
        "https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1"
    )
    assert resolve_bedrock_openai_base("https://bedrock-runtime.eu-west-1.amazonaws.com") == (
        "https://bedrock-runtime.eu-west-1.amazonaws.com/openai/v1"
    )


def test_prepare_azure_chat_request_uses_deployment_url():
    url, headers, payload = prepare_openai_chat_request(
        provider_type="Azure OpenAI",
        api_key="test-key",
        model="gpt-4o-prod",
        messages=[{"role": "user", "content": "hi"}],
        tools=[],
        endpoint="https://example.openai.azure.com",
    )
    assert url.startswith("https://example.openai.azure.com/openai/deployments/gpt-4o-prod/chat/completions")
    assert "api-version=" in url
    assert headers["api-key"] == "test-key"
    assert "model" not in payload


def test_prepare_openrouter_chat_request():
    url, headers, payload = prepare_openai_chat_request(
        provider_type="OpenRouter",
        api_key="or-key",
        model="anthropic/claude-3.5-sonnet",
        messages=[{"role": "user", "content": "hi"}],
        tools=[],
        endpoint="",
        base_url="https://openrouter.ai/api/v1",
    )
    assert url == "https://openrouter.ai/api/v1/chat/completions"
    assert headers["Authorization"] == "Bearer or-key"
    assert headers["HTTP-Referer"]
    assert payload["model"] == "anthropic/claude-3.5-sonnet"
