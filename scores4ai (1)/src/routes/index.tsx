import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import {
  getFeaturedTools,
  getToolsByCategory,
  getTopRankedTools,
  getTrendingTools,
  type CatalogTool,
} from "@/lib/catalog-api";

export const Route = createFileRoute("/")({ component: Home });

type SectionState = { title: string; tools: CatalogTool[]; error: string | null };

function Home() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [sections, setSections] = useState<SectionState[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      const [top, picks, trending, coding, image, research] = await Promise.all([
        getTopRankedTools(),
        getFeaturedTools(),
        getTrendingTools(),
        getToolsByCategory("coding-assistants"),
        getToolsByCategory("image-generation"),
        getToolsByCategory("research-search"),
      ]);
      if (cancelled) return;
      const errors = [top.error, picks.error, trending.error, coding.error, image.error, research.error].filter(Boolean) as string[];
      setGlobalError(errors[0] ?? null);
      setSections([
        { title: "Top overall rankings", tools: top.data, error: top.error },
        { title: "Editor picks", tools: picks.data, error: picks.error },
        { title: "Trending tools", tools: trending.data, error: trending.error },
        { title: "Best coding tools", tools: coding.data, error: coding.error },
        { title: "Best image tools", tools: image.data, error: image.error },
        { title: "Best research tools", tools: research.data, error: research.error },
        { title: "Recently verified", tools: [...top.data].sort((a,b)=> (b.lastVerifiedAt||"").localeCompare(a.lastVerifiedAt||"")).slice(0,12), error: null },
      ]);
      setIsLoading(false);
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  const filteredSections = useMemo(() => {
    const t = query.trim().toLowerCase();
    if (!t) return sections;
    return sections.map((section) => ({
      ...section,
      tools: section.tools.filter((tool) => tool.name.toLowerCase().includes(t) || tool.category.toLowerCase().includes(t)),
    }));
  }, [query, sections]);

  return <div className="min-h-screen"><Nav />
    <section className="relative overflow-hidden"><div className="absolute inset-0 grid-bg" />
      <div className="relative mx-auto max-w-7xl px-6 pb-12 pt-24 md:pt-32"><div className="mx-auto max-w-3xl text-center">
        <h1 className="font-display text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">Scores4AI Rankings</h1>
        <p className="mx-auto mt-6 max-w-xl text-base text-muted-foreground md:text-lg">Production catalog rankings backed by Supabase.</p>
        <div className="mx-auto mt-10 flex max-w-xl items-center gap-2 rounded-full glass-strong p-2 pl-5"><Search className="h-4 w-4 text-muted-foreground" />
          <input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search tools and categories" className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground" /></div>
      </div></div></section>

    <section className="mx-auto max-w-7xl px-6 pb-20">
      {isLoading ? <div className="rounded-2xl glass p-6">Loading rankings...</div> : globalError ?
        <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-5 text-sm text-destructive-foreground">Unable to load rankings right now. {globalError}</div>
        : filteredSections.every((s)=>s.tools.length===0) ?
          <div className="rounded-2xl glass p-6"><h3 className="font-display text-2xl font-semibold">No rankings available yet</h3></div>
          : <div className="space-y-10">{filteredSections.map((section)=> (
            <div key={section.title}>
              <h2 className="mb-4 font-display text-3xl font-semibold tracking-tight">{section.title}</h2>
              {section.error ? <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">Unable to load section.</div> : section.tools.length===0 ? <div className="rounded-xl glass p-4 text-sm text-muted-foreground">No rankings available yet</div> :
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">{section.tools.slice(0,12).map((tool)=><article key={`${section.title}-${tool.id}`} className="rounded-2xl glass p-5"><div className="text-xs text-muted-foreground">{tool.category}</div><h3 className="mt-2 font-display text-2xl font-semibold">{tool.name}</h3><p className="mt-2 text-sm text-muted-foreground">{tool.tagline ?? tool.description}</p><div className="mt-3 text-xs text-accent">Overall score: {tool.overallScore ?? "N/A"}</div></article>)}</div>}
            </div>
          ))}</div>}
    </section>
    <Footer />
  </div>;
}
