from app.services.model_usage_service import extract_llm_usage_details, extract_token_usage


def test_extract_llm_usage_details_openai():
    data = {"usage": {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200}}
    assert extract_llm_usage_details("OpenAI", data) == {
        "input_tokens": 120,
        "output_tokens": 80,
        "total_tokens": 200,
    }
    assert extract_token_usage("OpenAI", data) == 200


def test_extract_llm_usage_details_anthropic():
    data = {"usage": {"input_tokens": 50, "output_tokens": 25}}
    assert extract_llm_usage_details("Anthropic", data) == {
        "input_tokens": 50,
        "output_tokens": 25,
        "total_tokens": 75,
    }


def test_extract_llm_usage_details_gemini():
    data = {
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 15,
            "totalTokenCount": 25,
        }
    }
    assert extract_llm_usage_details("Gemini", data) == {
        "input_tokens": 10,
        "output_tokens": 15,
        "total_tokens": 25,
    }
