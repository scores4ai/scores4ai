import {
  readCachedOpenRouterModels,
  syncOpenRouterModels,
} from "../../src/lib/openrouter";
import { getServerSupabaseEnv } from "../../src/lib/supabase";

function json(statusCode: number, body: unknown) {
  return {
    statusCode,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=300, stale-while-revalidate=3600",
    },
    body: JSON.stringify(body),
  };
}

export async function handler(event: {
  httpMethod: string;
  queryStringParameters?: Record<string, string | undefined>;
  headers?: Record<string, string | undefined>;
}) {
  if (event.httpMethod !== "GET" && event.httpMethod !== "POST") {
    return json(405, { error: "Method not allowed" });
  }

  const force =
    event.queryStringParameters?.force === "true" ||
    event.httpMethod === "POST";
  const syncSecret = process.env.OPENROUTER_SYNC_CRON_SECRET;

  if (force && syncSecret) {
    const supplied =
      event.headers?.["x-sync-secret"] ?? event.headers?.["X-Sync-Secret"];
    if (supplied !== syncSecret) {
      return json(401, { error: "Missing or invalid sync secret" });
    }
  }

  try {
    if (!force) {
      const cached = await readCachedOpenRouterModels(getServerSupabaseEnv());
      if (cached.length > 0) {
        return json(200, {
          source: "cache",
          count: cached.length,
          models: cached,
        });
      }
    }

    const result = await syncOpenRouterModels({ force });
    return json(200, {
      source: result.source,
      count: result.models.length,
      models: result.models,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return json(500, { error: message });
  }
}
