import { DATA_FRESHNESS_MINUTES } from "@/lib/data-sources";
import type {
  OpenRouterModel,
  OpenRouterModelsResponse,
} from "@/lib/openrouter-types";

const OPENROUTER_MODELS_URL =
  "https://openrouter.ai/api/v1/models?output_modalities=all";

export async function fetchOpenRouterModels(fetcher: typeof fetch = fetch) {
  const response = await fetcher(OPENROUTER_MODELS_URL, {
    headers: {
      Accept: "application/json",
      "HTTP-Referer": "https://scores4.ai",
      "X-Title": "Scores4AI",
    },
  });

  if (!response.ok) {
    throw new Error(`OpenRouter models request failed: ${response.status}`);
  }

  const json = (await response.json()) as Partial<OpenRouterModelsResponse>;
  if (!json || !Array.isArray(json.data)) {
    console.error("[OpenRouter] Invalid models payload", {
      endpoint: OPENROUTER_MODELS_URL,
      hasJson: Boolean(json),
      dataType: typeof json?.data,
    });
    return { data: [] };
  }

  return { data: json.data };
}

export function pricePerMillionTokens(value?: string) {
  const tokenPrice = Number(value ?? 0);
  if (!Number.isFinite(tokenPrice)) return 0;
  return tokenPrice * 1_000_000;
}

export function freshnessWindowMs() {
  return DATA_FRESHNESS_MINUTES * 60 * 1000;
}

export function providerFromModelId(id: string) {
  return id.split("/")[0]?.replaceAll("-", " ") ?? "unknown";
}

export function normalizeOpenRouterModel(model: OpenRouterModel) {
  if (!model?.id || !model?.name) {
    console.error("[OpenRouter] Model missing required fields", {
      model,
      endpoint: OPENROUTER_MODELS_URL,
    });
  }

  return {
    openrouter_id: model?.id ?? "unknown-model-id",
    canonical_slug: model?.canonical_slug ?? model?.id ?? "unknown-model-id",
    name: model?.name ?? "Unknown Model",
    provider: providerFromModelId(model?.id ?? "unknown/model"),
    description: model.description ?? null,
    context_window:
      model.context_length ?? model.top_provider?.context_length ?? null,
    input_modalities: model.architecture?.input_modalities ?? [],
    output_modalities: model.architecture?.output_modalities ?? [],
    tokenizer: model.architecture?.tokenizer ?? null,
    instruct_type: model.architecture?.instruct_type ?? null,
    supported_parameters: model.supported_parameters ?? [],
    prompt_price_per_million: pricePerMillionTokens(model.pricing?.prompt),
    completion_price_per_million: pricePerMillionTokens(
      model.pricing?.completion,
    ),
    request_price: Number(model.pricing?.request ?? 0),
    max_completion_tokens: model.top_provider?.max_completion_tokens ?? null,
    is_moderated: model.top_provider?.is_moderated ?? null,
    openrouter_created_at: model.created
      ? new Date(model.created * 1000).toISOString()
      : null,
    expires_at: model.expiration_date ?? null,
  };
}
