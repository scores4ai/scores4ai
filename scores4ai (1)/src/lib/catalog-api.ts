import { env } from "@/lib/env";

export type CatalogTool = {
  id: string;
  slug: string;
  name: string;
  tagline: string | null;
  description: string;
  category: string;
  logoUrl: string | null;
  featured: boolean;
  editorPick: boolean;
  lastVerifiedAt: string | null;
  overallScore: number | null;
  trendScore: number | null;
};

export type CatalogResult<T> = {
  data: T;
  error: string | null;
};

function hasConfig() {
  return Boolean(env.supabaseUrl && env.supabaseAnonKey);
}

async function queryTools(query: string): Promise<CatalogResult<CatalogTool[]>> {
  if (!hasConfig()) return { data: [], error: null };
  try {
    const response = await fetch(`${env.supabaseUrl}/rest/v1/${query}`, {
      headers: {
        apikey: env.supabaseAnonKey,
        Authorization: `Bearer ${env.supabaseAnonKey}`,
      },
    });
    if (!response.ok) return { data: [], error: `Supabase request failed (${response.status})` };
    const rows = (await response.json()) as Array<any>;
    return {
      data: rows.map((row) => ({
        id: row.id,
        slug: row.slug,
        name: row.name,
        tagline: row.tagline ?? null,
        description: row.description ?? "",
        category: row.ai_categories?.name ?? "Uncategorized",
        logoUrl: row.logo_url ?? null,
        featured: Boolean(row.featured),
        editorPick: Boolean(row.editor_pick),
        lastVerifiedAt: row.last_verified_at ?? null,
        overallScore: row.ai_tool_scores?.overall_score ?? null,
        trendScore: row.ai_tool_trending_snapshots?.[0]?.trend_score ?? null,
      })),
      error: null,
    };
  } catch (error) {
    return { data: [], error: error instanceof Error ? error.message : "Unknown error" };
  }
}

export async function getFeaturedTools() {
  return queryTools("ai_tools?select=id,slug,name,tagline,description,logo_url,featured,editor_pick,last_verified_at,ai_categories(name),ai_tool_scores(overall_score),ai_tool_trending_snapshots(trend_score)&featured=eq.true&order=updated_at.desc&limit=12");
}

export async function getTopRankedTools() {
  return queryTools("ai_tools?select=id,slug,name,tagline,description,logo_url,featured,editor_pick,last_verified_at,ai_categories(name),ai_tool_scores(overall_score),ai_tool_trending_snapshots(trend_score)&order=ai_tool_scores.overall_score.desc.nullslast&limit=24");
}

export async function getToolsByCategory(categorySlug: string) {
  return queryTools(`ai_tools?select=id,slug,name,tagline,description,logo_url,featured,editor_pick,last_verified_at,ai_categories!inner(name,slug),ai_tool_scores(overall_score),ai_tool_trending_snapshots(trend_score)&ai_categories.slug=eq.${encodeURIComponent(categorySlug)}&limit=24`);
}

export async function searchTools(term: string) {
  if (!term.trim()) return getTopRankedTools();
  return queryTools(`ai_tools?select=id,slug,name,tagline,description,logo_url,featured,editor_pick,last_verified_at,ai_categories(name),ai_tool_scores(overall_score),ai_tool_trending_snapshots(trend_score)&or=(name.ilike.*${encodeURIComponent(term)}*,tagline.ilike.*${encodeURIComponent(term)}*)&limit=24`);
}

export async function getTrendingTools() {
  return queryTools("ai_tools?select=id,slug,name,tagline,description,logo_url,featured,editor_pick,last_verified_at,ai_categories(name),ai_tool_scores(overall_score),ai_tool_trending_snapshots(trend_score)&order=ai_tool_trending_snapshots.trend_score.desc.nullslast&limit=24");
}
