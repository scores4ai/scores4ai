import { env } from "@/lib/env";

export type TopTool = {
  id: string;
  slug: string;
  name: string;
  category: string;
  description: string;
  websiteUrl: string | null;
  overallScore: number;
};

export type TopToolsResult = {
  data: TopTool[];
  error: string | null;
};

export async function getTopTools(): Promise<TopToolsResult> {
  if (!env.supabaseUrl || !env.supabaseAnonKey) {
    return { data: [], error: null };
  }

  try {
    const response = await fetch(
      `${env.supabaseUrl}/rest/v1/ai_tools?select=id,slug,name,category,description,website_url,overall_score&order=overall_score.desc`,
      {
        headers: {
          apikey: env.supabaseAnonKey,
          Authorization: `Bearer ${env.supabaseAnonKey}`,
        },
      },
    );

    if (!response.ok) {
      console.error("[getTopTools] Supabase request failed", { status: response.status });
      return { data: [], error: `Supabase request failed (${response.status})` };
    }

    const rows = (await response.json()) as Array<{
      id: string;
      slug: string;
      name: string;
      category: string;
      description: string;
      website_url: string | null;
      overall_score: number | null;
    }>;

    return {
      data: rows.map((row) => ({
        id: row.id,
        slug: row.slug,
        name: row.name,
        category: row.category,
        description: row.description,
        websiteUrl: row.website_url,
        overallScore: row.overall_score ?? 0,
      })),
      error: null,
    };
  } catch (error) {
    console.error("[getTopTools] Unexpected error", error);
    return {
      data: [],
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}
