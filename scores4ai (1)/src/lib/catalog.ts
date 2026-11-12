import { tools as demoTools, getTool as getDemoTool, rails as demoRails } from "@/lib/data";
import { env, logRuntimeEnvAudit } from "@/lib/env";

export type CatalogState = {
  tools: typeof demoTools;
  rails: typeof demoRails;
  isDemo: boolean;
  reason: string;
};

function resolveCatalogState(): CatalogState {
  logRuntimeEnvAudit();

  if (env.useDemoData) {
    console.warn("[runtime-audit] demo mode activated", {
      reason: "VITE_USE_DEMO_DATA === 'true'",
      file: "src/lib/catalog.ts",
    });

    return {
      tools: demoTools,
      rails: demoRails,
      isDemo: true,
      reason: "VITE_USE_DEMO_DATA === 'true'",
    };
  }

  console.info("[runtime-audit] demo mode disabled", {
    reason: "VITE_USE_DEMO_DATA !== 'true'",
    file: "src/lib/catalog.ts",
  });

  return {
    tools: [],
    rails: [],
    isDemo: false,
    reason: "Demo data disabled. Awaiting live Supabase-backed catalog.",
  };
}

export const catalogState = resolveCatalogState();

export const catalogTools = catalogState.tools;
export const catalogRails = catalogState.rails;

export function getCatalogTool(id: string) {
  if (!catalogState.isDemo) return undefined;
  return getDemoTool(id);
}
