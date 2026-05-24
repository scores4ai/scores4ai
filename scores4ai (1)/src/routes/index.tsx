import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { env } from "@/lib/env";

type FeaturedTool = {
  id: string;
  name: string;
  category: string;
  description: string;
  logo: string;
  benchmarkScore: number;
  communityScore: number;
  programmerScore: number;
  pricing: string;
};

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "scores4ai — Production rankings" },
      {
        name: "description",
        content:
          "Production-first AI rankings with transparent source states and verified data ingestion.",
      },
    ],
  }),
  component: Home,
});

function Home() {
  const [query, setQuery] = useState("");
  const [tools, setTools] = useState<FeaturedTool[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadFeaturedTools() {
      const hasSupabaseConfig = Boolean(env.supabaseUrl && env.supabaseAnonKey);
      if (!hasSupabaseConfig) {
        if (!isCancelled) {
          setTools([]);
          setError(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        const url = `${env.supabaseUrl}/rest/v1/tools?select=id,name,category,description,pricing_type,metadata&order=updated_at.desc&limit=12`;
        const response = await fetch(url, {
          headers: {
            apikey: env.supabaseAnonKey,
            Authorization: `Bearer ${env.supabaseAnonKey}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to load tools (${response.status})`);
        }

        const rows = (await response.json()) as Array<{
          id: string;
          name: string;
          category: string;
          description: string | null;
          pricing_type: string | null;
          metadata?: {
            logo?: string;
            benchmark_score?: number;
            community_score?: number;
            programmer_score?: number;
          };
        }>;

        if (isCancelled) return;

        setTools(
          rows.map((row) => ({
            id: row.id,
            name: row.name,
            category: row.category,
            description: row.description ?? "No description available.",
            logo: row.metadata?.logo ?? "🧠",
            benchmarkScore: row.metadata?.benchmark_score ?? 0,
            communityScore: row.metadata?.community_score ?? 0,
            programmerScore: row.metadata?.programmer_score ?? 0,
            pricing: row.pricing_type ?? "Unknown",
          })),
        );
      } catch (loadError) {
        if (!isCancelled) {
          setTools([]);
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load rankings.",
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadFeaturedTools();
    return () => {
      isCancelled = true;
    };
  }, []);

  const filteredTools = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return tools;
    return tools.filter(
      (tool) =>
        tool.name.toLowerCase().includes(normalized) ||
        tool.category.toLowerCase().includes(normalized),
    );
  }, [query, tools]);

  return (
    <div className="min-h-screen">
      <Nav />

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 pt-24 md:pt-32">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">
              Scores4AI Rankings
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-base text-muted-foreground md:text-lg">
              Discover production-ready AI tools with transparent scoring and
              pricing metadata.
            </p>
            <div className="mx-auto mt-10 flex max-w-xl items-center gap-2 rounded-full glass-strong p-2 pl-5">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search tools and categories"
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-20">
        <div className="mb-6">
          <div className="text-xs uppercase tracking-wider text-accent">Featured tools</div>
          <h2 className="mt-1 font-display text-3xl font-semibold tracking-tight md:text-4xl">
            Latest ranking entries
          </h2>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="rounded-2xl glass p-5 animate-pulse">
                <div className="h-4 w-24 rounded bg-white/10" />
                <div className="mt-3 h-6 w-40 rounded bg-white/10" />
                <div className="mt-3 h-4 w-full rounded bg-white/10" />
                <div className="mt-2 h-4 w-5/6 rounded bg-white/10" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-5 text-sm text-destructive-foreground">
            Unable to load rankings right now. {error}
          </div>
        ) : filteredTools.length === 0 ? (
          <div className="rounded-2xl glass p-6">
            <h3 className="font-display text-2xl font-semibold">No rankings available yet</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Rankings will appear after tool data is ingested into Supabase.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredTools.map((tool) => (
              <article key={tool.id} className="rounded-2xl glass p-5">
                <div className="flex items-center justify-between">
                  <span className="text-2xl" aria-hidden="true">{tool.logo}</span>
                  <span className="text-[11px] uppercase tracking-wider text-muted-foreground">{tool.category}</span>
                </div>
                <h3 className="mt-3 font-display text-2xl font-semibold">{tool.name}</h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{tool.description}</p>
                <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                  <div className="rounded-lg bg-secondary/40 p-2">B: {tool.benchmarkScore}</div>
                  <div className="rounded-lg bg-secondary/40 p-2">C: {tool.communityScore}</div>
                  <div className="rounded-lg bg-secondary/40 p-2">P: {tool.programmerScore}</div>
                </div>
                <div className="mt-3 text-xs uppercase tracking-wider text-accent">Pricing: {tool.pricing}</div>
              </article>
            ))}
          </div>
        )}
      </section>

      <Footer />
    </div>
  );
}
