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

type RankingsSearch = {
  q?: string;
};

export const Route = createFileRoute("/rankings")({
  validateSearch: (search: Record<string, unknown>): RankingsSearch => {
    const q = typeof search.q === "string" ? search.q.trim() : "";
    return { q: q || undefined };
  },
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

const searchStopWords = new Set(["ai", "a", "an", "and", "best", "for", "the"]);

function normalizeSearchText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function tokenMatchesSearchableText(token: string, searchableText: string) {
  if (searchableText.includes(token)) return true;

  const singularToken =
    token.length > 3 && token.endsWith("s") ? token.slice(0, -1) : token;

  return singularToken !== token && searchableText.includes(singularToken);
}

function Rankings() {
  const { q } = Route.useSearch();
  const searchTerm = q ?? "";
  const searchTokens = useMemo(
    () =>
      normalizeSearchText(searchTerm)
        .split(" ")
        .filter((token) => token && !searchStopWords.has(token)),
    [searchTerm],
  );
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
    if (searchTokens.length > 0) {
      filteredTools = filteredTools.filter((tool) => {
        const searchableText = normalizeSearchText(
          [
            tool.name,
            tool.developer,
            tool.category,
            tool.tagline,
            tool.description,
            tool.pricing,
            tool.verdict,
            tool.scores.value >= 85 ? "low cost cheap budget value" : "",
            tool.scores.privacy >= 85 ? "private privacy local self host" : "",
            tool.scores.speed >= 90 ? "fast speed low latency" : "",
            ...(tool.tags ?? []),
            ...(tool.modality ?? []),
          ].join(" "),
        );

        return searchTokens.every((token) =>
          tokenMatchesSearchableText(token, searchableText),
        );
      });
    }

    const intentWeights = weightsForIntent(intent);
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
  }, [filter, sort, openOnly, intent, searchTokens]);

  return (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="text-xs uppercase tracking-wider text-accent">
          Transparent rankings · decision workflow
        </div>
        <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight">
          Shortlist AI tools without pretending demo data is live
        </h1>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Search by job, filter by category, and sort by the weighted signal you
          care about. Cards are intentionally labeled so seed records never look
          like verified production rankings.
        </p>

        <div className="mt-8">
          <DataNotice compact />
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {[
            [
              "Source labels",
              "Every card shows live, cached, estimated, or demo status before you trust the score.",
            ],
            [
              "OpenRouter-ready",
              "Model IDs and pricing are designed to be replaced by scheduled OpenRouter sync rows.",
            ],
            [
              "Action-first",
              "Use rankings to shortlist, then open Compare to test prompts and monthly spend.",
            ],
          ].map(([title, body]) => (
            <div
              key={title}
              className="rounded-xl border border-border bg-card/40 p-4"
            >
              <div className="text-sm font-medium">{title}</div>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {body}
              </p>
            </div>
          ))}
        </div>
        <div className="mt-8">
          <ScoreExplainer />
        </div>

        <form
          action="/rankings"
          method="get"
          className="mt-8 rounded-2xl glass p-5"
          role="search"
        >
          <label
            htmlFor="rankings-search"
            className="text-xs uppercase tracking-wider text-accent"
          >
            Search the catalog
          </label>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input
              id="rankings-search"
              name="q"
              defaultValue={searchTerm}
              placeholder="Claude, coding, image, open source..."
              className="min-w-0 flex-1 rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none placeholder:text-muted-foreground focus:border-accent"
            />
            <button
              type="submit"
              className="rounded-xl bg-accent px-5 py-3 text-sm font-medium text-accent-foreground glow-accent"
            >
              Search rankings
            </button>
            {searchTerm && (
              <a
                href="/rankings"
                className="rounded-xl border border-border px-5 py-3 text-center text-sm text-muted-foreground hover:text-foreground"
              >
                Clear
              </a>
            )}
          </div>
          {searchTerm && (
            <p className="mt-3 text-sm text-muted-foreground">
              Showing {list.length} result{list.length === 1 ? "" : "s"} for “
              {searchTerm}”. Filters and sorting still apply.
            </p>
          )}
        </form>

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

        {list.length > 0 ? (
          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {list.map(({ tool, displayScore }, i) => (
              <ToolCard
                key={tool.id}
                tool={tool}
                index={i}
                displayScore={displayScore}
                displayScoreLabel="Transparent score"
              />
            ))}
          </div>
        ) : (
          <div className="mt-10 rounded-2xl border border-border bg-card/40 p-8 text-center">
            <h2 className="font-display text-2xl font-semibold">
              No matching AI tools yet
            </h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
              Try a broader search, clear category filters, or check back after
              live OpenRouter and community data sources are connected.
            </p>
            <a
              href="/rankings"
              className="mt-5 inline-flex rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground"
            >
              Reset rankings
            </a>
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
