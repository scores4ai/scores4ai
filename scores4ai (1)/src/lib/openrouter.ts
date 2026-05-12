import {
  getServerSupabaseEnv,
  supabaseRest,
  type SupabaseEnv,
} from "./supabase";

export type OpenRouterModel = {
  id: string;
  name?: string;
  description?: string;
  context_length?: number;
  architecture?: {
    modality?: string;
    tokenizer?: string;
    instruct_type?: string | null;
  };
  pricing?: {
    prompt?: string;
    completion?: string;
    request?: string;
    image?: string;
    web_search?: string;
    internal_reasoning?: string;
    input_cache_read?: string;
  };
  top_provider?: Record<string, unknown>;
  per_request_limits?: Record<string, unknown> | null;
};

type OpenRouterResponse = {
  data: OpenRouterModel[];
};

export type CachedModelRecord = {
  slug: string;
  provider: string;
  name: string;
  description: string | null;
  context_window: number | null;
  modalities: string[];
  tokenizer: string | null;
  input_price_per_million: number | null;
  output_price_per_million: number | null;
  cached_input_price_per_million: number | null;
  pricing_unit: "token";
  openrouter_id: string;
  source: "openrouter";
  raw_source: OpenRouterModel;
  is_active: boolean;
  synced_at: string;
};

const OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models";

function pricePerMillion(value?: string): number | null {
  if (!value) return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return null;
  return parsed * 1_000_000;
}

function splitProvider(openrouterId: string) {
  const [provider, ...rest] = openrouterId.split("/");
  return {
    provider: provider || "unknown",
    modelSlug: rest.join("/") || openrouterId,
  };
}

function toModalities(model: OpenRouterModel): string[] {
  const modality = model.architecture?.modality;
  if (!modality) return [];
  return modality
    .split("+")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function normalizeOpenRouterModel(
  model: OpenRouterModel,
): CachedModelRecord {
  const { provider, modelSlug } = splitProvider(model.id);
  const now = new Date().toISOString();

  return {
    slug: model.id
      .replace(/[^a-zA-Z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .toLowerCase(),
    provider,
    name: model.name ?? modelSlug,
    description: model.description ?? null,
    context_window: model.context_length ?? null,
    modalities: toModalities(model),
    tokenizer: model.architecture?.tokenizer ?? null,
    input_price_per_million: pricePerMillion(model.pricing?.prompt),
    output_price_per_million: pricePerMillion(model.pricing?.completion),
    cached_input_price_per_million: pricePerMillion(
      model.pricing?.input_cache_read,
    ),
    pricing_unit: "token",
    openrouter_id: model.id,
    source: "openrouter",
    raw_source: model,
    is_active: true,
    synced_at: now,
  };
}

export async function fetchOpenRouterModels(
  apiKey?: string,
): Promise<OpenRouterModel[]> {
  const headers = new Headers({ accept: "application/json" });
  if (apiKey) headers.set("authorization", `Bearer ${apiKey}`);
  if (process.env.OPENROUTER_SITE_URL)
    headers.set("HTTP-Referer", process.env.OPENROUTER_SITE_URL);
  if (process.env.OPENROUTER_APP_NAME)
    headers.set("X-Title", process.env.OPENROUTER_APP_NAME);

  const response = await fetch(OPENROUTER_MODELS_URL, { headers });
  if (!response.ok) {
    throw new Error(`OpenRouter models fetch failed with ${response.status}`);
  }

  const payload = (await response.json()) as OpenRouterResponse;
  return payload.data ?? [];
}

export async function readCachedOpenRouterModels(supabaseEnv: SupabaseEnv) {
  return supabaseRest<CachedModelRecord[]>(supabaseEnv, "models", {
    query:
      "?select=slug,provider,name,description,context_window,modalities,tokenizer,input_price_per_million,output_price_per_million,cached_input_price_per_million,pricing_unit,openrouter_id,source,raw_source,is_active,synced_at&source=eq.openrouter&is_active=eq.true&order=provider.asc,name.asc",
  });
}

export async function cacheOpenRouterModels(
  models: OpenRouterModel[],
  supabaseEnv: SupabaseEnv = getServerSupabaseEnv(),
) {
  const records = models.map(normalizeOpenRouterModel);
  if (records.length === 0) return [];

  return supabaseRest<CachedModelRecord[]>(supabaseEnv, "models", {
    method: "POST",
    query: "?on_conflict=openrouter_id",
    prefer: "resolution=merge-duplicates,return=representation",
    body: JSON.stringify(records),
  });
}

export async function syncOpenRouterModels(options: { force?: boolean } = {}) {
  const supabaseEnv = getServerSupabaseEnv();
  const cacheMinutes = Number(
    process.env.OPENROUTER_MODELS_CACHE_MINUTES ?? 60,
  );

  if (!options.force) {
    const cached = await readCachedOpenRouterModels(supabaseEnv);
    const newestSync = cached
      .map((model) => (model.synced_at ? Date.parse(model.synced_at) : 0))
      .sort((a, b) => b - a)[0];
    if (newestSync && Date.now() - newestSync < cacheMinutes * 60_000) {
      return { source: "cache" as const, models: cached };
    }
  }

  const openRouterModels = await fetchOpenRouterModels(
    process.env.OPENROUTER_API_KEY,
  );
  const cachedModels = await cacheOpenRouterModels(
    openRouterModels,
    supabaseEnv,
  );
  return { source: "openrouter" as const, models: cachedModels };
}
