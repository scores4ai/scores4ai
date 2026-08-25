import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { DataNotice } from "@/components/site/DataNotice";
import { PricingCalculator } from "@/components/site/PricingCalculator";
import { PromptLab } from "@/components/site/PromptLab";
import { ScoreMeter } from "@/components/site/Score";
import { tools, getTool } from "@/lib/data";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare AI Models — scores4ai" },
      {
        name: "description",
        content:
          "Side-by-side AI model comparison with radar charts, prompt testing, pricing estimates, and transparent scoring.",
      },
    ],
  }),
  component: Compare,
});

const COLORS = ["var(--accent)", "var(--reliable)", "var(--elite)"];

function Compare() {
  const [chartReady, setChartReady] = useState(false);
  const [picks, setPicks] = useState<string[]>([
    "gpt-5",
    "claude-4",
    "gemini-3",
  ]);
  const selected = picks
    .map(getTool)
    .filter(Boolean) as (typeof tools)[number][];

  const dims = [
    "intelligence",
    "speed",
    "ease",
    "value",
    "creativity",
    "hallucination",
  ] as const;
  const data = dims.map((d) => {
    const row: Record<string, number | string> = {
      k: d[0].toUpperCase() + d.slice(1),
    };
    selected.forEach((t) => (row[t.name] = t.scores[d]));
    return row;
  });

  const setSlot = (i: number, id: string) =>
    setPicks((p) => p.map((x, idx) => (idx === i ? id : x)));

  useEffect(() => {
    setChartReady(true);
  }, []);

  return (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="text-xs uppercase tracking-wider text-accent">
          Side-by-side
        </div>
        <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight">
          Compare any AI, head to head
        </h1>

        <p className="mt-3 max-w-2xl text-muted-foreground">
          Compare benchmark dimensions, transparent score components, pricing
          assumptions, and repeatable prompts. Demo seed data is labeled until
          connected to live OpenRouter + Supabase feeds.
        </p>
        <div className="mt-8">
          <DataNotice compact />
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {picks.map((id, i) => (
            <div key={i} className="rounded-2xl glass p-5">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Slot {i + 1}
              </div>
              <select
                value={id}
                onChange={(e) => setSlot(i, e.target.value)}
                className="mt-2 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
              >
                {tools.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              {selected[i] && (
                <div className="mt-4">
                  <div
                    className="font-display text-3xl font-semibold"
                    style={{ color: COLORS[i] }}
                  >
                    {selected[i].scores.ai}
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px] text-muted-foreground">
                    <div>
                      <span className="block font-display text-sm text-foreground">
                        {selected[i].scores.ai}
                      </span>
                      AI
                    </div>
                    <div>
                      <span className="block font-display text-sm text-foreground">
                        {selected[i].scores.community}
                      </span>
                      Community
                    </div>
                    <div>
                      <span className="block font-display text-sm text-foreground">
                        {selected[i].scores.programmer}
                      </span>
                      Programmer
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {selected[i].developer}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-8 rounded-2xl glass p-6">
          <h2 className="font-display text-xl font-semibold">
            Capability radar
          </h2>
          <div className="mt-4 h-96">
            {chartReady ? (
              <ResponsiveContainer>
                <RadarChart data={data}>
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
                  {selected.map((t, i) => (
                    <Radar
                      key={t.id}
                      dataKey={t.name}
                      stroke={COLORS[i]}
                      fill={COLORS[i]}
                      fillOpacity={0.18}
                    />
                  ))}
                  <Legend
                    wrapperStyle={{
                      color: "var(--muted-foreground)",
                      fontSize: 12,
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="grid h-full place-items-center rounded-2xl border border-border bg-card/40 text-sm text-muted-foreground">
                Capability chart loads in the browser with your selected tools.
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <PromptLab />
          <PricingCalculator />
        </div>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {selected.map((t, i) => (
            <div key={t.id} className="rounded-2xl glass p-6">
              <div className="flex items-center justify-between">
                <h3 className="font-display text-lg font-semibold">{t.name}</h3>
                <span className="text-xs text-muted-foreground">
                  {t.pricing}
                </span>
              </div>
              <div className="mt-4 space-y-3">
                <ScoreMeter
                  label="Intelligence"
                  value={t.scores.intelligence}
                  color={COLORS[i]}
                />
                <ScoreMeter
                  label="Speed"
                  value={t.scores.speed}
                  color={COLORS[i]}
                />
                <ScoreMeter
                  label="Value"
                  value={t.scores.value}
                  color={COLORS[i]}
                />
                <ScoreMeter
                  label="Anti-Hallucination"
                  value={t.scores.hallucination}
                  color={COLORS[i]}
                />
                <ScoreMeter
                  label="Privacy"
                  value={t.scores.privacy}
                  color={COLORS[i]}
                />
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-lg bg-secondary/50 p-2">
                  <div className="text-muted-foreground">Context</div>
                  <div className="font-medium">{t.contextWindow ?? "—"}</div>
                </div>
                <div className="rounded-lg bg-secondary/50 p-2">
                  <div className="text-muted-foreground">Open</div>
                  <div className="font-medium">
                    {t.openSource ? "Yes" : "No"}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
