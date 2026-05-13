import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { ScoreExplainer } from "@/components/site/ScoreExplainer";
import { ToolCard } from "@/components/site/ToolCard";
import { tools } from "@/lib/data";
import {
  intentOptions,
  transparentScore,
  weightsForIntent,
  type RankingIntent,
} from "@/lib/scoring";

export const Route = createFileRoute("/rankings")({
  head: () => ({
    meta: [
      { title: "AI Rankings — scores4ai" },
      {
        name: "description",
        content:
          "Transparent demo rankings of AI tools, models, and agents, with live-data labels when verified sources are connected.",
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
  const [intent, setIntent] = useState<RankingIntent>("coding");

  const list = useMemo(() => {
    let filteredTools = tools.filter((tool) =>
      filter === "All" ? true : tool.category === filter,
    );
    if (openOnly)
      filteredTools = filteredTools.filter((tool) => tool.openSource);

    const intentWeights = weightsForIntent(intent);
    const scoredTools = filteredTools.map((tool) => {
      const scoreDetails = transparentScore(tool, intentWeights);
      return {
        tool,
        displayScore: scoreDetails.score,
        scoreDetails,
      };
    });
    const scoredTools = filteredTools.map((tool) => ({
      tool,
      displayScore: transparentScore(tool, intentWeights).score,
    }));
    const key = (
      {
        "AI score": (item: (typeof scoredTools)[number]) => item.displayScore,
        Trending: (item: (typeof scoredTools)[number]) => item.tool.trend,
        Community: (item: (typeof scoredTools)[number]) =>
          item.tool.scores.community,
        Programmer: (item: (typeof scoredTools)[number]) =>
          item.tool.scores.programmer,
        Speed: (item: (typeof scoredTools)[number]) => item.tool.scores.speed,
        Value: (item: (typeof scoredTools)[number]) => item.tool.scores.value,
      } as const
    )[sort];
    return scoredTools.sort((a, b) => key(b) - key(a));
  }, [filter, sort, openOnly, intent]);

  return (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="text-xs uppercase tracking-wider text-accent">
          Demo rankings · live-data ready
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

        <div className="mt-8 rounded-2xl glass p-5">
          <div className="text-xs uppercase tracking-wider text-accent">
            Personalized rankings
          </div>
          <h2 className="mt-1 font-display text-2xl font-semibold">
            What are you using AI for?
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {intentOptions.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setIntent(option)}
                className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                  intent === option
                    ? "border-accent bg-accent text-accent-foreground"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            Rankings dynamically recalculate with transparent weights for{" "}
            {intent}. Change the sliders in Transparent Scoring to audit the
            formula.
          </p>
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
          {list.map(({ tool, displayScore, scoreDetails }, i) => (
          {list.map(({ tool, displayScore }, i) => (
            <ToolCard
              key={tool.id}
              tool={tool}
              index={i}
              displayScore={displayScore}
              displayScoreLabel="Transparent score"
              scoreDetails={scoreDetails}
            />
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
