const OPENROUTER_MODELS_URL =
  "https://openrouter.ai/api/v1/models?output_modalities=all";

function hasUsableValue(name) {
  const value = process.env[name];
  return Boolean(
    value &&
    !value.includes("your-") &&
    !value.includes("example") &&
    !value.includes("placeholder"),
  );
}

function pricePerMillion(value) {
  const tokenPrice = Number(value ?? 0);
  return Number.isFinite(tokenPrice) ? tokenPrice * 1_000_000 : 0;
}

function providerFromId(id) {
  return id.split("/")[0]?.replaceAll("-", " ") ?? "unknown";
}

function normalizeOpenRouterModel(model) {
  return {
    id: model.id,
    name: model.name,
    provider: providerFromId(model.id),
    description: model.description ?? "OpenRouter model metadata.",
    contextWindow:
      model.context_length ?? model.top_provider?.context_length ?? null,
    inputPricePerMillion: pricePerMillion(model.pricing?.prompt),
    outputPricePerMillion: pricePerMillion(model.pricing?.completion),
    inputModalities: model.architecture?.input_modalities ?? [],
    outputModalities: model.architecture?.output_modalities ?? [],
    supportedParameters: model.supported_parameters ?? [],
    sourceStatus: "live",
    sourceLabel: "OpenRouter",
    lastSyncedAt: new Date().toISOString(),
  };
}

function normalizeSupabaseModel(model) {
  return {
    id: model.openrouter_id ?? model.id,
    name: model.name,
    provider: model.provider ?? "unknown",
    description: model.description ?? "Cached Supabase model metadata.",
    contextWindow: model.context_window ?? null,
    inputPricePerMillion: Number(model.prompt_price_per_million ?? 0),
    outputPricePerMillion: Number(model.completion_price_per_million ?? 0),
    inputModalities: model.input_modalities ?? [],
    outputModalities: model.output_modalities ?? [],
    supportedParameters: model.supported_parameters ?? [],
    sourceStatus:
      model.source_status === "live" ? "cached" : model.source_status,
    sourceLabel: "Supabase Cache",
    lastSyncedAt: model.last_synced_at ?? null,
  };
}

async function fetchOpenRouterModels() {
  const keyDetected = hasUsableValue("OPENROUTER_API_KEY");
  const headers = {
    Accept: "application/json",
    "HTTP-Referer": process.env.VITE_SITE_URL ?? "https://scores4.ai",
    "X-Title": "Scores4AI",
  };

  if (keyDetected) {
    headers.Authorization = `Bearer ${process.env.OPENROUTER_API_KEY}`;
  }

  console.log(
    `[openrouter-models] Fetching OpenRouter models. keyDetected=${keyDetected}`,
  );

  const response = await fetch(OPENROUTER_MODELS_URL, { headers });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenRouter ${response.status}: ${body.slice(0, 300)}`);
  }

  const payload = await response.json();
  const records = (payload.data ?? [])
    .map(normalizeOpenRouterModel)
    .filter((model) => model.name && model.id)
    .slice(0, 24);

  console.log(
    `[openrouter-models] OpenRouter fetch success rows=${records.length}`,
  );
  return records;
}

async function fetchSupabaseCachedModels() {
  const configured =
    hasUsableValue("SUPABASE_URL") &&
    hasUsableValue("SUPABASE_SERVICE_ROLE_KEY");

  if (!configured) {
    return {
      configured: false,
      ok: false,
      records: [],
      detail: "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Netlify.",
    };
  }

  const url = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  try {
    const response = await fetch(
      `${url}/rest/v1/models?select=openrouter_id,name,provider,description,context_window,prompt_price_per_million,completion_price_per_million,input_modalities,output_modalities,supported_parameters,source_status,last_synced_at&order=last_synced_at.desc&limit=24`,
      {
        headers: {
          apikey: serviceRoleKey,
          Authorization: `Bearer ${serviceRoleKey}`,
        },
      },
    );

    if (!response.ok) {
      const body = await response.text();
      return {
        configured: true,
        ok: false,
        records: [],
        detail: `Supabase REST returned ${response.status}. Run supabase/full_setup.sql, then run npm run sync:openrouter. ${body.slice(0, 200)}`,
      };
    }

    const rows = await response.json();
    const records = rows.map(normalizeSupabaseModel);
    console.log(`[openrouter-models] Supabase cache rows=${records.length}`);
    return {
      configured: true,
      ok: true,
      records,
      detail:
        records.length > 0
          ? "Supabase cache contains model rows."
          : "Supabase is connected but models is empty. Run npm run sync:openrouter or wait for the scheduled sync.",
    };
  } catch (error) {
    return {
      configured: true,
      ok: false,
      records: [],
      detail: `Supabase cache check failed: ${error instanceof Error ? error.message : "unknown error"}`,
    };
  }
}

export default async () => {
  const keyDetected = hasUsableValue("OPENROUTER_API_KEY");
  const startedAt = Date.now();
  const supabase = await fetchSupabaseCachedModels();
  let openRouter = {
    keyDetected,
    ok: false,
    status: "not_checked",
    detail: "OpenRouter fetch has not completed.",
  };
  let records = [];
  let dataMode = "demo";

  try {
    records = await fetchOpenRouterModels();
    openRouter = {
      keyDetected,
      ok: true,
      status: "success",
      detail: keyDetected
        ? "OPENROUTER_API_KEY detected and OpenRouter fetch succeeded."
        : "OpenRouter fetch succeeded without a key; add OPENROUTER_API_KEY for authenticated live execution.",
    };
    dataMode = "live";
  } catch (error) {
    openRouter = {
      keyDetected,
      ok: false,
      status: "failure",
      detail:
        error instanceof Error ? error.message : "OpenRouter fetch failed.",
    };
    console.error(
      `[openrouter-models] OpenRouter fetch failed: ${openRouter.detail}`,
    );

    if (supabase.records.length > 0) {
      records = supabase.records;
      dataMode = "cached";
    }
  }

  if (dataMode === "live" && supabase.ok) {
    console.log(
      `[openrouter-models] Serving live OpenRouter rows with Supabase connected. durationMs=${Date.now() - startedAt}`,
    );
  } else {
    console.log(
      `[openrouter-models] dataMode=${dataMode} rows=${records.length} durationMs=${Date.now() - startedAt}`,
    );
  }

  return new Response(
    JSON.stringify({
      dataMode,
      generatedAt: new Date().toISOString(),
      records,
      checks: {
        openRouter,
        supabase: {
          configured: supabase.configured,
          ok: supabase.ok,
          detail: supabase.detail,
        },
      },
      nextActions:
        dataMode === "demo"
          ? [
              openRouter.ok
                ? "Run Supabase setup and sync if you want cached fallback rows."
                : "Fix OpenRouter server fetch before claiming live data.",
              supabase.ok
                ? "Run npm run sync:openrouter or wait for scheduled sync."
                : "Run supabase/full_setup.sql and verify SUPABASE_SERVICE_ROLE_KEY.",
            ]
          : [],
    }),
    {
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
      },
    },
  );
};
