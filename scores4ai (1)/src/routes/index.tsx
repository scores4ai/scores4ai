import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { getTopTools, type TopTool } from "@/lib/catalog-api";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  const [tools, setTools] = useState<TopTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      const result = await getTopTools();
      if (cancelled) return;
      setTools(result.data);
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

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 pt-24 md:pt-32">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">
              Scores4AI Rankings
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-base text-muted-foreground md:text-lg">
              Production rankings backed by Supabase.
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-20">
        <h2 className="mb-4 font-display text-3xl font-semibold tracking-tight">
          Top overall rankings
        </h2>

        {loading ? (
          <div className="rounded-2xl glass p-6">Loading rankings...</div>
        ) : error ? (
          <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-5 text-sm text-destructive-foreground">
            Unable to load rankings.
          </div>
        ) : tools.length === 0 ? (
          <div className="rounded-2xl glass p-6">No rankings available yet.</div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tools.slice(0, 12).map((tool) => (
              <article key={tool.id} className="rounded-2xl glass p-5">
                <div className="text-xs text-muted-foreground">{tool.category}</div>
                <h3 className="mt-2 font-display text-2xl font-semibold">{tool.name}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{tool.description}</p>
                <div className="mt-3 text-xs text-accent">
                  Overall score: {tool.overallScore}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <Footer />
    </div>
  );
}
