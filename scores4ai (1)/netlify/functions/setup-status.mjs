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

function checkEnv(name, label, required = true) {
  const configured = hasUsableValue(name);
  return {
    id: name,
    label,
    configured,
    required,
    status: configured ? "ready" : required ? "missing" : "optional",
  };
}

async function checkSupabaseModelsTable() {
  if (
    !hasUsableValue("SUPABASE_URL") ||
    !hasUsableValue("SUPABASE_SERVICE_ROLE_KEY")
  ) {
    return {
      id: "supabase_models_table",
      label: "Supabase models table reachable",
      configured: false,
      required: true,
      status: "missing",
      detail: "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.",
    };
  }

  const url = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  try {
    const response = await fetch(`${url}/rest/v1/models?select=id&limit=1`, {
      headers: {
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
      },
    });

    return {
      id: "supabase_models_table",
      label: "Supabase models table reachable",
      configured: response.ok,
      required: true,
      status: response.ok ? "ready" : "missing",
      detail: response.ok
        ? "Schema is reachable with the service role key."
        : `Supabase REST returned ${response.status}. Run supabase/full_setup.sql and verify service credentials.`,
    };
  } catch (error) {
    return {
      id: "supabase_models_table",
      label: "Supabase models table reachable",
      configured: false,
      required: true,
      status: "missing",
      detail: `Supabase check failed: ${error instanceof Error ? error.message : "unknown error"}`,
    };
  }
}

async function checkOpenRouterModelsApi() {
  try {
    const response = await fetch(OPENROUTER_MODELS_URL, {
      headers: {
        Accept: "application/json",
        "HTTP-Referer": process.env.VITE_SITE_URL ?? "https://scores4.ai",
        "X-Title": "Scores4AI",
      },
    });

    return {
      id: "openrouter_models_api",
      label: "OpenRouter Models API reachable",
      configured: response.ok,
      required: true,
      status: response.ok ? "ready" : "missing",
      detail: response.ok
        ? "OpenRouter model metadata endpoint is reachable server-side."
        : `OpenRouter returned ${response.status}.`,
    };
  } catch (error) {
    return {
      id: "openrouter_models_api",
      label: "OpenRouter Models API reachable",
      configured: false,
      required: true,
      status: "missing",
      detail: `OpenRouter check failed: ${error instanceof Error ? error.message : "unknown error"}`,
    };
  }
}

export default async () => {
  const checks = [
    checkEnv("VITE_SUPABASE_URL", "Public Supabase URL"),
    checkEnv("VITE_SUPABASE_ANON_KEY", "Public Supabase anon key"),
    checkEnv("SUPABASE_URL", "Server Supabase URL"),
    checkEnv("SUPABASE_SERVICE_ROLE_KEY", "Server Supabase service role key"),
    checkEnv(
      "OPENROUTER_API_KEY",
      "OpenRouter API key for future live execution",
      false,
    ),
    await checkSupabaseModelsTable(),
    await checkOpenRouterModelsApi(),
  ];

  const requiredChecks = checks.filter((check) => check.required);
  const missingRequired = requiredChecks.filter((check) => !check.configured);
  const optionalMissing = checks.filter(
    (check) => !check.required && !check.configured,
  );

  return new Response(
    JSON.stringify({
      ok: missingRequired.length === 0,
      generatedAt: new Date().toISOString(),
      summary: {
        ready: requiredChecks.length - missingRequired.length,
        missingRequired: missingRequired.length,
        optionalMissing: optionalMissing.length,
      },
      checks,
      nextActions: missingRequired.map((check) => check.label),
    }),
    {
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
      },
    },
  );
};
