import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, Flame, MessageSquare, TrendingUp } from "lucide-react";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";

export const Route = createFileRoute("/community")({
  head: () => ({
    meta: [
      { title: "Community — scores4ai" },
      {
        name: "description",
        content:
          "Trending discussions, top reviewers, and viral prompt trends.",
      },
    ],
  }),
  component: Community,
});

const discussions = [
  {
    t: "Anyone else switching from Cursor to Zed + Claude?",
    c: 412,
    v: 1820,
    tag: "Coding",
  },
  {
    t: "How should Scores4AI weight math benchmarks vs coding reliability?",
    c: 287,
    v: 2410,
    tag: "Benchmarks",
  },
  {
    t: "What evidence should a vetted programmer review require?",
    c: 631,
    v: 980,
    tag: "Agents",
  },
  {
    t: "Best local model setup for privacy-sensitive work?",
    c: 154,
    v: 740,
    tag: "Local",
  },
  {
    t: "Share prompt patterns that are reproducible across video tools",
    c: 902,
    v: 5210,
    tag: "Video",
  },
];

const reviewers = [
  { n: "@karpathy_fan", rep: 14820, b: "Top Reviewer" },
  { n: "@research_ana", rep: 11210, b: "Methodology reviewer" },
  { n: "@vibe_coder", rep: 9870, b: "Prompt Wizard" },
  { n: "@open_source_dev", rep: 8420, b: "OSS Champion" },
  { n: "@ml_skeptic", rep: 7610, b: "Bench Master" },
];

const switches = [
  ["ChatGPT", "Claude 4 Opus", "+38%"],
  ["Copilot", "Cursor", "+71%"],
  ["AutoGPT", "Browser Use", "+204%"],
  ["Midjourney", "Sora 2", "+19%"],
];

function Community() {
  return (
    <div className="min-h-screen">
      <Nav />
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="text-xs uppercase tracking-wider text-accent">
          Community · activity stream
        </div>
        <h1 className="mt-2 font-display text-5xl font-semibold tracking-tight">
          What the AI world is evaluating
        </h1>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Discussion and reviewer modules are shown with current integration status.
        </p>

        <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_360px]">
          <main className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Flame className="h-4 w-4 text-accent" /> Trending discussions
            </div>
            {discussions.map((d) => (
              <div
                key={d.t}
                className="group flex items-center justify-between rounded-2xl glass p-5 hover:border-white/15"
              >
                <div>
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
                    <span className="rounded bg-secondary px-1.5 py-0.5">
                      {d.tag}
                    </span>
                    <span>· 2h ago</span>
                  </div>
                  <h3 className="mt-1 font-display text-lg font-semibold group-hover:text-accent">
                    {d.t}
                  </h3>
                  <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      {d.v}
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      {d.c}
                    </span>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
              </div>
            ))}
          </main>

          <aside className="space-y-6">
            <div className="rounded-2xl glass p-5">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">
                Top AI Reviewers
              </div>
              <ol className="mt-4 space-y-3">
                {reviewers.map((r, i) => (
                  <li key={r.n} className="flex items-center gap-3">
                    <span className="font-display text-lg w-5 text-muted-foreground">
                      {i + 1}
                    </span>
                    <div className="grid h-8 w-8 place-items-center rounded-full bg-white/10 text-xs">
                      {r.n[1].toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm">{r.n}</div>
                      <div className="text-[10px] text-muted-foreground">
                        {r.b}
                      </div>
                    </div>
                    <div className="font-display text-sm">
                      {r.rep.toLocaleString()}
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="rounded-2xl glass p-5">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">
                People are switching
              </div>
              <ul className="mt-4 space-y-3 text-sm">
                {switches.map(([from, to, pct]) => (
                  <li key={from} className="flex items-center justify-between">
                    <span>
                      <span className="text-muted-foreground line-through">
                        {from}
                      </span>
                      <span className="mx-1.5 text-muted-foreground">→</span>
                      <span>{to}</span>
                    </span>
                    <span className="text-elite text-xs">{pct}</span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </div>
      <Footer />
    </div>
  );
}
