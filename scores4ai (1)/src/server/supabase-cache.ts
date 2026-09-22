import { fetchOpenRouterModels, normalizeOpenRouterModel } from "./openrouter";

export const MODEL_REFRESH_MS = 12 * 60 * 60 * 1000;
export const PRICING_REFRESH_MS = 24 * 60 * 60 * 1000;

type SupabaseConfig = {
  url: string;
  serviceRoleKey: string;
};

function getSupabaseConfig(
  env: Record<string, string | undefined> = process.env,
) {
  const url = env.SUPABASE_URL ?? env.VITE_SUPABASE_URL;
  const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !serviceRoleKey) return undefined;
  return { url, serviceRoleKey } satisfies SupabaseConfig;
}

async function supabaseFetch(
  config: SupabaseConfig,
  path: string,
  init: RequestInit = {},
) {
  const response = await fetch(`${config.url}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: config.serviceRoleKey,
      Authorization: `Bearer ${config.serviceRoleKey}`,
      "content-type": "application/json",
      Prefer: "resolution=merge-duplicates,return=minimal",
      ...init.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(
      `Supabase cache request failed (${response.status}): ${body}`,
    );
  }

  return response;
}

export async function syncOpenRouterModelsToSupabase(
  env: Record<string, string | undefined> = process.env,
) {
  const config = getSupabaseConfig(env);
  if (!config) {
    throw new Error(
      "SUPABASE_URL/VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for sync.",
    );
  }

  const payload = await fetchOpenRouterModels();
  const syncedAt = new Date().toISOString();
  const sourceModels = Array.isArray(payload?.data) ? payload.data : [];
  if (!Array.isArray(payload?.data)) {
    console.error("[Supabase Sync] OpenRouter response missing data array", {
      payload,
      endpoint: "openrouter models",
    });
  }

  const rows = sourceModels.map((model) => ({
    ...normalizeOpenRouterModel(model),
    raw_openrouter_payload: model,
    source_status: "live",
    last_synced_at: syncedAt,
    pricing_last_synced_at: syncedAt,
  }));

  for (let index = 0; index < rows.length; index += 200) {
    const chunk = rows.slice(index, index + 200);
    await supabaseFetch(config, "models?on_conflict=openrouter_id", {
      method: "POST",
      body: JSON.stringify(chunk),
    });
  }

  await supabaseFetch(
    config,
    "model_sources?on_conflict=source_type,source_url",
    {
      method: "POST",
      body: JSON.stringify({
        source_type: "api",
        source_url: "https://openrouter.ai/api/v1/models?output_modalities=all",
        verification_status: "Verified",
        last_checked_at: syncedAt,
        metadata: {
          rows: rows.length,
          refreshHours: 12,
          pricingRefreshHours: 24,
        },
      }),
    },
  );

  return { count: rows.length, syncedAt };
}
