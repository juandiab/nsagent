export const AI_PROVIDER_HINTS = {
  OpenAI: {
    required: false,
    hint: 'Leave empty — uses https://api.openai.com/v1',
    example: '',
    hostNote: 'Cloud API — no local endpoint needed'
  },
  Anthropic: {
    required: false,
    hint: 'Leave empty — uses https://api.anthropic.com/v1',
    example: '',
    hostNote: 'Cloud API — no local endpoint needed'
  },
  Gemini: {
    required: false,
    hint: 'Leave empty — uses Google Generative Language API',
    example: '',
    hostNote: 'Cloud API — get an API key from Google AI Studio'
  },
  Grok: {
    required: false,
    hint: 'Leave empty — uses https://api.x.ai/v1 (xAI)',
    example: '',
    hostNote: 'Cloud API — get an API key from console.x.ai'
  },
  DeepSeek: {
    required: false,
    hint: 'Leave empty — uses https://api.deepseek.com/v1',
    example: '',
    hostNote: 'Cloud API — get an API key from platform.deepseek.com'
  },
  OpenRouter: {
    required: false,
    hint: 'Leave empty — uses https://openrouter.ai/api/v1',
    example: '',
    hostNote: 'Cloud API — one key for many models; get an API key from openrouter.ai/keys'
  },
  'Azure OpenAI': {
    required: true,
    hint: 'Azure resource root URL (not the deployment path)',
    example: 'https://your-resource.openai.azure.com',
    hostNote:
      'Use the resource URL from Azure AI Foundry. Model dropdown lists deployments — pick a deployment name, not the base model SKU.'
  },
  'AWS Bedrock': {
    required: true,
    hint: 'AWS region code or full Bedrock OpenAI-compatible base URL',
    example: 'us-east-1',
    hostNote:
      'Uses the Bedrock OpenAI-compatible API (…/openai/v1). Paste a Bedrock API key or long-term key from the AWS console. IAM access keys are not supported yet.'
  },
  'LM Studio': {
    required: true,
    hint: 'OpenAI-compatible base URL — LM Studio uses /v1',
    example: 'http://host.docker.internal:1234/v1',
    hostNote:
      'API URL only — do not open in a browser (that causes GET / and favicon noise in LM Studio logs). Use the app at http://localhost:5173. Docker: http://host.docker.internal:1234/v1. Enable "Serve on local network" in LM Studio.'
  },
  'OpenAI-Compatible': {
    required: true,
    hint: 'Full base URL with /v1 — host/IP, port, and path to the compatible API',
    example: 'http://127.0.0.1:8080/v1',
    hostNote: 'Example: http://10.0.0.5:8080/v1 or https://my-llm.local/v1'
  }
}

export function getProviderHint(providerType) {
  return AI_PROVIDER_HINTS[providerType] || AI_PROVIDER_HINTS.OpenAI
}
