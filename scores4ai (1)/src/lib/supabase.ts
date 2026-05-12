export type SupabaseEnv = {
  url: string;
  anonKey?: string;
  serviceRoleKey?: string;
};

export type SupabaseError = {
  message: string;
  details?: string;
  hint?: string;
  code?: string;
};

export function getPublicSupabaseEnv(): SupabaseEnv | null {
  const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

  if (!url || !anonKey) return null;
  return { url, anonKey };
}

export function getServerSupabaseEnv(
  env: NodeJS.ProcessEnv = process.env,
): SupabaseEnv {
  const url = env.SUPABASE_URL ?? env.VITE_SUPABASE_URL;
  const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url) throw new Error("Missing SUPABASE_URL or VITE_SUPABASE_URL");
  if (!serviceRoleKey) throw new Error("Missing SUPABASE_SERVICE_ROLE_KEY");

  return { url, serviceRoleKey };
}

function getRestUrl(url: string, table: string, query = "") {
  const cleanUrl = url.replace(/\/$/, "");
  return `${cleanUrl}/rest/v1/${table}${query}`;
}

export async function supabaseRest<T>(
  env: SupabaseEnv,
  table: string,
  init: RequestInit & { query?: string; prefer?: string } = {},
): Promise<T> {
  const key = env.serviceRoleKey ?? env.anonKey;
  if (!key) throw new Error("Missing Supabase API key");

  const headers = new Headers(init.headers);
  headers.set("apikey", key);
  headers.set("authorization", `Bearer ${key}`);
  headers.set("content-type", "application/json");
  if (init.prefer) headers.set("prefer", init.prefer);

  const response = await fetch(getRestUrl(env.url, table, init.query), {
    ...init,
    headers,
  });

  if (!response.ok) {
    let message = `Supabase request failed with ${response.status}`;
    try {
      const error = (await response.json()) as SupabaseError;
      message = error.message || message;
    } catch {
      message = await response.text();
    }
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
