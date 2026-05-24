import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { getTopRankedTools, searchTools, type CatalogTool } from "@/lib/catalog-api";

export const Route = createFileRoute("/rankings")({ component: Rankings });

function Rankings() {
  const [query, setQuery] = useState("");
  const [tools, setTools] = useState<CatalogTool[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const result = query.trim() ? await searchTools(query) : await getTopRankedTools();
      if (cancelled) return;
      setTools(result.data);
      setError(result.error);
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, [query]);

  const sorted = useMemo(() => [...tools].sort((a,b)=>(b.overallScore ?? 0)-(a.overallScore ?? 0)), [tools]);

  return <div className="min-h-screen"><Nav />
    <div className="mx-auto max-w-7xl px-6 py-16">
      <h1 className="font-display text-5xl font-semibold tracking-tight">AI Rankings</h1>
      <input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search rankings" className="mt-4 w-full rounded-lg border border-border bg-card px-3 py-2" />
      {loading ? <div className="mt-8 rounded-xl glass p-4">Loading rankings...</div> : error ? <div className="mt-8 rounded-xl border border-destructive/40 bg-destructive/10 p-4">Unable to load rankings right now.</div> : sorted.length===0 ? <div className="mt-8 rounded-xl glass p-4">No rankings available yet</div> :
      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">{sorted.map((tool)=><article key={tool.id} className="rounded-2xl glass p-5"><div className="text-xs text-muted-foreground">{tool.category}</div><h2 className="mt-2 font-display text-2xl font-semibold">{tool.name}</h2><p className="mt-2 text-sm text-muted-foreground">{tool.tagline ?? tool.description}</p><div className="mt-3 text-xs text-accent">Overall score: {tool.overallScore ?? 'N/A'}</div></article>)}</div>}
    </div><Footer />
  </div>;
}
