export const env = {
  useDemoData: import.meta.env.VITE_USE_DEMO_DATA === "true",
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL,
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY,
  openrouterApiKey: import.meta.env.VITE_OPENROUTER_API_KEY,
  isProduction: import.meta.env.PROD,
};

export function getLiveDataEnvError(): string | null {
  if (env.useDemoData) return null;

  const missing: string[] = [];
  if (!env.supabaseUrl) missing.push("VITE_SUPABASE_URL");
  if (!env.supabaseAnonKey) missing.push("VITE_SUPABASE_ANON_KEY");

  if (missing.length > 0) {
    return `Live data is unavailable because required env vars are missing: ${missing.join(", ")}.`;
  }

  return "Live data mode is enabled, but no Supabase-backed card data loader is configured.";
}
