import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ExternalLink, Globe, Sparkles } from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { DataNotice } from "@/components/site/DataNotice";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { PricingCalculator } from "@/components/site/PricingCalculator";
import { PromptLab } from "@/components/site/PromptLab";
import { ScoreGauge, ScoreMeter } from "@/components/site/Score";
import { ToolCard } from "@/components/site/ToolCard";
import { verdictColor, type Tool } from "@/lib/data";
import { getCatalogTool as getTool, catalogTools as tools, catalogState } from "@/lib/catalog";

export const Route = createFileRoute("/tool/$id")({
  loader: ({ params }): { tool: Tool } => {
    const tool = getTool(params.id);
    if (!tool) throw notFound();
    return { tool };
  },
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: `${loaderData.tool.name} — Reviews & Score | scores4ai` },
          { name: "description", content: loaderData.tool.tagline },
          {
            property: "og:title",
            content: `${loaderData.tool.name} on scores4ai`,
          },
          { property: "og:description", content: loaderData.tool.tagline },
        ]
      : [],
  }),
  component: ToolPage,
  notFoundComponent: () => (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-3xl px-6 py-32 text-center">
        <h1 className="font-display text-4xl">Tool not found</h1>
        <Link to="/" className="mt-6 inline-block text-accent">
          ← Back home
        </Link>
      </div>
    </div>
  ),
  errorComponent: ({ error }) => (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-3xl px-6 py-32 text-center text-muted-foreground">
        {error.message}
      </div>
    </div>
  ),
});

const tabs = [
  "Overview",
  "Reviews",
  "Benchmarks",
  "Comparisons",
  "Use Cases",
  "Prompt Lab",
  "Sources",
  "Discussions",
  "Alternatives",
  "Pricing",
  "API",
];

function ToolPage() {
  const { tool } = Route.useLoaderData() as { tool: Tool };

  const radar = [
    { k: "Intelligence", v: tool.scores.intelligence },
    { k: "Speed", v: tool.scores.speed },
    { k: "Ease", v: tool.scores.ease },
    { k: "Value", v: tool.scores.value },
    { k: "Privacy", v: tool.scores.privacy },
    { k: "Creativity", v: tool.scores.creativity },
  ];

  const alternatives = tools
    .filter((t) => t.id !== tool.id && t.category === tool.category)
    .slice(0, 4);

  return (
    <div className="min-h-screen">
      <Nav />

      {/* Header */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 grid-bg opacity-60" />
        <div className="relative mx-auto max-w-7xl px-6 py-16">
          <Link
            to="/"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Discover
          </Link>
          <div className="mt-6 flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
            <div className="flex items-start gap-5">
              <div className="grid h-20 w-20 place-items-center rounded-2xl bg-gradient-to-br from-white/15 to-white/5 font-display text-3xl font-semibold">
                {tool.name.slice(0, 1)}
              </div>
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-muted-foreground">
                  <span>{tool.category}</span>
                  <span>·</span>
                  <span>{tool.developer}</span>
                  <span>·</span>
                  <span>Released {tool.released}</span>
                </div>
                <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight">
                  {tool.name}
                </h1>
                <p className="mt-2 max-w-xl text-muted-foreground">
                  {tool.tagline}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {tool.tags.map((t) => (
                    <span
                      key={t}
                      className="rounded-md bg-secondary px-2 py-0.5 text-xs text-muted-foreground"
                    >
                      {t}
                    </span>
                  ))}
                  <span className="rounded-md border border-border px-2 py-0.5 text-xs">
                    {tool.pricing}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div
                className="rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-wider"
                style={{
                  color: verdictColor[tool.verdict],
                  background: `color-mix(in oklab, ${verdictColor[tool.verdict]} 15%, transparent)`,
                  border: `1px solid color-mix(in oklab, ${verdictColor[tool.verdict]} 30%, transparent)`,
                }}
              >
                {tool.verdict}
              </div>
              <ScoreGauge value={tool.scores.ai} label="AI score" />
              <a
                href={tool.website}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background"
              >
                <Globe className="h-4 w-4" /> Visit
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Tabs */}
      <div className="sticky top-[65px] z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="scrollbar-hide mx-auto flex max-w-7xl gap-6 overflow-x-auto px-6">
          {tabs.map((t, i) => (
            <button
              key={t}
              className={`whitespace-nowrap py-3 text-sm transition-colors ${
                i === 0
                  ? "border-b-2 border-accent text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="mx-auto mt-6 max-w-7xl px-6">
        <DataNotice compact />
      </div>
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-12 lg:grid-cols-[1fr_360px]">
        <main>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl glass p-6"
          >
            <h2 className="font-display text-xl font-semibold">Overview</h2>
            <p className="mt-3 text-muted-foreground">{tool.description}</p>
          </motion.div>

          <div className="mt-6 rounded-2xl glass p-6">
            <h2 className="font-display text-xl font-semibold">
              Score breakdown
            </h2>
            <div className="mt-6 grid gap-x-10 gap-y-5 md:grid-cols-2">
              <ScoreMeter
                label="AI score"
                value={tool.scores.ai}
                color="var(--accent)"
              />
              <ScoreMeter
                label="Community"
                value={tool.scores.community}
                color="var(--reliable)"
              />
              <ScoreMeter
                label="Programmer"
                value={tool.scores.programmer}
                color="var(--experimental)"
              />
              <ScoreMeter label="Speed" value={tool.scores.speed} />
              <ScoreMeter
                label="Intelligence"
                value={tool.scores.intelligence}
              />
              <ScoreMeter label="Ease of Use" value={tool.scores.ease} />
              <ScoreMeter label="Value" value={tool.scores.value} />
              <ScoreMeter
                label="Anti-Hallucination"
                value={tool.scores.hallucination}
                color="var(--elite)"
              />
              <ScoreMeter
                label="Privacy"
                value={tool.scores.privacy}
                color="var(--reliable)"
              />
              <ScoreMeter
                label="Creativity"
                value={tool.scores.creativity}
                color="var(--experimental)"
              />
            </div>
          </div>

          <div className="mt-6 rounded-2xl glass p-6">
            <h2 className="font-display text-xl font-semibold">
              Capability profile
            </h2>
            <div className="mt-2 h-72">
              <ResponsiveContainer>
                <RadarChart data={radar}>
                  <PolarGrid stroke="oklch(1 0 0 / 0.1)" />
                  <PolarAngleAxis
                    dataKey="k"
                    tick={{ fill: "oklch(0.7 0.01 270)", fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    tick={false}
                    axisLine={false}
                    domain={[0, 100]}
                  />
                  <Radar
                    dataKey="v"
                    stroke="var(--accent)"
                    fill="var(--accent)"
                    fillOpacity={0.3}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-6">
            <PromptLab />
          </div>

          <div className="mt-6">
            <PricingCalculator />
          </div>

          <div className="mt-6 rounded-2xl glass p-6">
            <div className="text-xs uppercase tracking-wider text-accent">
              Sources tab
            </div>
            <h2 className="mt-1 font-display text-xl font-semibold">
              Verification sources
            </h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {[
                [
                  "Official pricing source",
                  "OpenRouter Models API",
                  "Verified",
                ],
                [
                  "Benchmark source",
                  "Scores4AI benchmark snapshots",
                  "Estimated",
                ],
                [
                  "API source",
                  tool.openRouterId
                    ? tool.openRouterId
                    : "Awaiting OpenRouter match",
                  tool.openRouterId ? "Verified" : "Needs Review",
                ],
                [
                  "Last checked",
                  tool.lastVerified ?? "Needs live verification",
                  tool.sourceStatus === "demo" ? "Needs Review" : "Verified",
                ],
              ].map(([label, value, status]) => (
                <div
                  key={label}
                  className="rounded-xl bg-secondary/40 p-4 text-sm"
                >
                  <div className="text-xs uppercase tracking-wider text-muted-foreground">
                    {label}
                  </div>
                  <div className="mt-1 font-medium">{value}</div>
                  <div className="mt-2 inline-flex rounded-full border border-border px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                    {status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 rounded-2xl glass p-6">
            <h2 className="font-display text-xl font-semibold">
              Top community reviews
            </h2>
            <div className="mt-4 space-y-4">
              {[
                {
                  u: "alex.dev",
                  r: 9.2,
                  t: "Replaced three tools in my workflow. Worth every cent.",
                },
                {
                  u: "research_ana",
                  r: 8.7,
                  t: "Best-in-class for long context. Citations are clean.",
                },
                {
                  u: "vibe_coder",
                  r: 7.9,
                  t: "Hallucinates less than peers but still needs supervision on edge cases.",
                },
              ].map((r) => (
                <div key={r.u} className="rounded-xl bg-secondary/40 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-full bg-white/10 text-xs">
                        {r.u.slice(0, 1).toUpperCase()}
                      </div>
                      <div className="text-sm font-medium">@{r.u}</div>
                    </div>
                    <div className="font-display text-sm">{r.r}</div>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{r.t}</p>
                </div>
              ))}
            </div>
          </div>
        </main>

        <aside className="space-y-4">
          <div className="rounded-2xl glass p-5">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">
              Quick facts
            </div>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Pricing</dt>
                <dd>{tool.pricing}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Released</dt>
                <dd>{tool.released}</dd>
              </div>
              {tool.contextWindow && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Context</dt>
                  <dd>{tool.contextWindow}</dd>
                </div>
              )}
              {tool.modality && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Modality</dt>
                  <dd>{tool.modality.join(", ")}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Open source</dt>
                <dd>{tool.openSource ? "Yes" : "No"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Data status</dt>
                <dd>{tool.sourceStatus}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Evidence</dt>
                <dd>{tool.evidenceCount || "Demo"}</dd>
              </div>
            </dl>
          </div>

          <div className="rounded-2xl glass p-5">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-accent" /> AI Summary
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Reviewers consistently praise {tool.name}'s{" "}
              {tool.tags[0] ?? "core capability"}. Watch for{" "}
              {tool.scores.hallucination < 80
                ? "occasional hallucinations"
                : "edge-case latency"}{" "}
              on complex tasks.
            </p>
          </div>

          <div className="rounded-2xl glass p-5">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">
              Alternatives
            </div>
            <div className="mt-3 space-y-3">
              {alternatives.map((a) => (
                <Link
                  key={a.id}
                  to="/tool/$id"
                  params={{ id: a.id }}
                  className="flex items-center justify-between rounded-lg p-2 hover:bg-secondary"
                >
                  <div className="flex items-center gap-3">
                    <div className="grid h-8 w-8 place-items-center rounded-md bg-white/10 text-xs">
                      {a.name.slice(0, 1)}
                    </div>
                    <div className="text-sm">{a.name}</div>
                  </div>
                  <span className="font-display text-sm">{a.scores.ai}</span>
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </div>

      <section className="mx-auto max-w-7xl px-6 pb-16">
        <h2 className="font-display text-2xl font-semibold">
          More like {tool.name}
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {alternatives.map((a, i) => (
            <ToolCard key={a.id} tool={a} index={i} />
          ))}
        </div>
      </section>

      <Footer />
    </div>
  );
}
