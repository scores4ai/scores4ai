import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { getTopTools, type TopTool } from "@/lib/catalog-api";

export const Route = createFileRoute("/rankings")({ component: Rankings });

function Rankings() {
  const [tools, setTools] = useState<TopTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const result = await getTopTools();
      if (cancelled) return;
      const sorted = [...result.data].sort((a, b) => b.overallScore - a.overallScore);
      setTools(sorted);
      setError(result.error);
      setLoading(false);
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-7xl px-6 py-16">
        <h1 className="font-display text-5xl font-semibold tracking-tight">AI Rankings</h1>
        {loading ? (
          <div className="mt-8 rounded-xl glass p-4">Loading rankings...</div>
        ) : error ? (
          <div className="mt-8 rounded-xl border border-destructive/40 bg-destructive/10 p-4">
            Unable to load rankings.
          </div>
        ) : tools.length === 0 ? (
          <div className="mt-8 rounded-xl glass p-4">No rankings available yet.</div>
        ) : (
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tools.map((tool) => (
              <article key={tool.id} className="rounded-2xl glass p-5">
                <div className="text-xs text-muted-foreground">{tool.category}</div>
                <h2 className="mt-2 font-display text-2xl font-semibold">{tool.name}</h2>
                <p className="mt-2 text-sm text-muted-foreground">{tool.description}</p>
                <div className="mt-3 text-xs text-accent">Overall score: {tool.overallScore}</div>
              </article>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
