const OPENROUTER_MODELS_URL =
  "https://openrouter.ai/api/v1/models?output_modalities=all";

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
}

function pricePerMillion(value) {
  const tokenPrice = Number(value ?? 0);
  return Number.isFinite(tokenPrice) ? tokenPrice * 1_000_000 : 0;
}

function providerFromId(id) {
  return id.split("/")[0]?.replaceAll("-", " ") ?? "unknown";
}

function normalize(model, syncedAt) {
  return {
    openrouter_id: model.id,
    canonical_slug: model.canonical_slug ?? model.id,
    name: model.name,
    provider: providerFromId(model.id),
    description: model.description ?? null,
    context_window:
      model.context_length ?? model.top_provider?.context_length ?? null,
    input_modalities: model.architecture?.input_modalities ?? [],
    output_modalities: model.architecture?.output_modalities ?? [],
    tokenizer: model.architecture?.tokenizer ?? null,
    instruct_type: model.architecture?.instruct_type ?? null,
    supported_parameters: model.supported_parameters ?? [],
    prompt_price_per_million: pricePerMillion(model.pricing?.prompt),
    completion_price_per_million: pricePerMillion(model.pricing?.completion),
    request_price: Number(model.pricing?.request ?? 0),
    max_completion_tokens: model.top_provider?.max_completion_tokens ?? null,
    is_moderated: model.top_provider?.is_moderated ?? null,
    openrouter_created_at: model.created
      ? new Date(model.created * 1000).toISOString()
      : null,
    expires_at: model.expiration_date ?? null,
    raw_openrouter_payload: model,
    source_status: "live",
    last_synced_at: syncedAt,
    pricing_last_synced_at: syncedAt,
  };
}

async function supabaseFetch(path, init = {}) {
  const url = required("SUPABASE_URL");
  const serviceRoleKey = required("SUPABASE_SERVICE_ROLE_KEY");
  const response = await fetch(`${url}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: serviceRoleKey,
      Authorization: `Bearer ${serviceRoleKey}`,
      "content-type": "application/json",
      Prefer: "resolution=merge-duplicates,return=minimal",
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`Supabase ${response.status}: ${await response.text()}`);
  }
}

export default async () => {
  const response = await fetch(OPENROUTER_MODELS_URL, {
    headers: {
      Accept: "application/json",
      "HTTP-Referer": process.env.VITE_SITE_URL ?? "https://scores4.ai",
      "X-Title": "Scores4AI",
    },
  });
  if (!response.ok) {
    throw new Error(`OpenRouter ${response.status}: ${await response.text()}`);
  }

  const payload = await response.json();
  const syncedAt = new Date().toISOString();
  const rows = payload.data.map((model) => normalize(model, syncedAt));

  for (let index = 0; index < rows.length; index += 200) {
    await supabaseFetch("models?on_conflict=openrouter_id", {
      method: "POST",
      body: JSON.stringify(rows.slice(index, index + 200)),
    });
  }

  await supabaseFetch("model_sources?on_conflict=source_type,source_url", {
    method: "POST",
    body: JSON.stringify({
      source_type: "api",
      source_url: OPENROUTER_MODELS_URL,
      verification_status: "Verified",
      last_checked_at: syncedAt,
      metadata: {
        rows: rows.length,
        refreshHours: 12,
        pricingRefreshHours: 24,
      },
    }),
  });

  return new Response(
    JSON.stringify({ count: rows.length, syncedAt, source: "OpenRouter" }),
    { headers: { "content-type": "application/json" } },
  );
};

export const config = {
  schedule: "0 */12 * * *",
};
