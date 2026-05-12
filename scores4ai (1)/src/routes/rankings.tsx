import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { ScoreExplainer } from "@/components/site/ScoreExplainer";
import { ToolCard } from "@/components/site/ToolCard";
import { tools } from "@/lib/data";

export const Route = createFileRoute("/rankings")({
  head: () => ({
    meta: [
      { title: "AI Rankings — scores4ai" },
      {
        name: "description",
        content: "Live rankings of AI tools, models, and agents.",
      },
    ],
  }),
  component: Rankings,
});

const filters = [
  "All",
  "LLM",
  "Coding Tool",
  "AI Agent",
  "Image",
  "Video",
  "Audio",
  "Research",
  "Productivity",
  "Infrastructure",
  "Companion",
];
const sorts = [
  "AI score",
  "Trending",
  "Community",
  "Programmer",
  "Speed",
  "Value",
] as const;

function Rankings() {
  const [filter, setFilter] = useState("All");
  const [sort, setSort] = useState<(typeof sorts)[number]>("AI score");
  const [openOnly, setOpenOnly] = useState(false);

  const list = useMemo(() => {
    let l = tools.filter((t) =>
      filter === "All" ? true : t.category === filter,
    );
    if (openOnly) l = l.filter((t) => t.openSource);
    const key = (
      {
        "AI score": (t: (typeof tools)[number]) => t.scores.ai,
        Trending: (t: (typeof tools)[number]) => t.trend,
        Community: (t: (typeof tools)[number]) => t.scores.community,
        Programmer: (t: (typeof tools)[number]) => t.scores.programmer,
        Speed: (t: (typeof tools)[number]) => t.scores.speed,
        Value: (t: (typeof tools)[number]) => t.scores.value,
      } as const
    )[sort];
    return [...l].sort((a, b) => key(b) - key(a));
  }, [filter, sort, openOnly]);

  return (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="text-xs uppercase tracking-wider text-accent">
          Live rankings
        </div>
        <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight">
          The complete AI leaderboard
        </h1>
        <p className="mt-3 max-w-xl text-muted-foreground">
          Filter by category, sort by what matters. Updated continuously from
          community votes, vetted programmer scores, and benchmark feeds. Demo
          records are explicitly labeled until live data is connected.
        </p>

        <div className="mt-8">
          <DataNotice compact />
        </div>
        <div className="mt-8">
          <ScoreExplainer />
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-2">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                filter === f
                  ? "border-accent bg-accent text-accent-foreground"
                  : "border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {f}
            </button>
          ))}
          <div className="mx-3 h-5 w-px bg-border" />
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={openOnly}
              onChange={(e) => setOpenOnly(e.target.checked)}
            />
            Open source only
          </label>
          <div className="ml-auto flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Sort by</span>
            <select
              value={sort}
              onChange={(e) =>
                setSort(e.target.value as (typeof sorts)[number])
              }
              className="rounded-md border border-border bg-card px-2 py-1.5"
            >
              {sorts.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((t, i) => (
            <ToolCard key={t.id} tool={t} index={i} />
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
