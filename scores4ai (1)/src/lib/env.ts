export const env = {
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL,
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY,
  openRouterApiKey: import.meta.env.VITE_OPENROUTER_API_KEY,
  useDemoData: import.meta.env.VITE_USE_DEMO_DATA === "true",
  mode: import.meta.env.MODE,
  isProduction: import.meta.env.PROD,
};

export function logRuntimeEnvAudit() {
  console.info("[runtime-audit] environment", {
    mode: env.mode,
    isProduction: env.isProduction,
    hasSupabaseUrl: Boolean(env.supabaseUrl),
    hasSupabaseAnonKey: Boolean(env.supabaseAnonKey),
    hasOpenRouterApiKey: Boolean(env.openRouterApiKey),
    useDemoData: env.useDemoData,
  });
}
